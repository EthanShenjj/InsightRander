from flask import Blueprint, jsonify, request
from models import db, ProductUpdate, CompetitiveLandscape
from collectors.changelog_scrapers import (
    PostHogChangelogCollector,
    MixpanelChangelogCollector,
    AmplitudeChangelogCollector
)
from collectors.sensorsdata import SensorsDataCollector
from services.feishu_sync import FeishuBitableSync
from datetime import datetime, timedelta
import threading
import uuid
import time

api_bp = Blueprint('api', __name__)

# 存储后台任务状态
_jobs = {}


def _run_collection(job_id, app, days=None, products=None):
    """后台线程执行采集任务"""
    _jobs[job_id] = {"status": "running", "progress": [], "summary": [], "started_at": time.time()}

    all_collectors = [
        PostHogChangelogCollector(),
        MixpanelChangelogCollector(),
        AmplitudeChangelogCollector(),
        SensorsDataCollector(),
    ]
    
    # 过滤选定的产品
    if products:
        collectors = [c for c in all_collectors if c.product_name in products]
    else:
        collectors = all_collectors

    all_new_updates = []

    with app.app_context():
        for collector in collectors:
            _jobs[job_id]["progress"].append(f"正在采集 {collector.product_name}...")
            try:
                t0 = time.time()
                # 如果采集器支持 days 参数，则传递
                if hasattr(collector, 'collect_with_days'):
                    updates = collector.collect_with_days(days) if days else collector.collect()
                else:
                    updates = collector.collect()
                
                elapsed = round(time.time() - t0, 2)

                new_count = 0
                updated_count = 0
                for u in updates:
                    # 使用 source_url 作为唯一标识进行查找
                    record = ProductUpdate.query.filter_by(source_url=u['source_url']).first()
                    
                    if record:
                        # 覆盖已有记录：更新核心字段
                        record.product = u['product']
                        record.source_type = u['source_type']
                        record.title = u['title']
                        record.content = u['content']
                        record.publish_time = u['publish_time']
                        record.content_hash = u['content_hash']
                        record.raw_data_dict = u.get('raw_data', {})
                        # 重置 AI 分析字段，确保能触发重新分析（如果后续有自动分析逻辑）
                        # record.summary = None
                        # record.tags = None
                        # record.update_type = None
                        updated_count += 1
                    else:
                        # 创建新记录
                        record = ProductUpdate(
                            product=u['product'],
                            source_type=u['source_type'],
                            title=u['title'],
                            content=u['content'],
                            source_url=u['source_url'],
                            publish_time=u['publish_time'],
                            content_hash=u['content_hash']
                        )
                        record.raw_data_dict = u.get('raw_data', {})
                        db.session.add(record)
                        new_count += 1
                    
                    db.session.flush()
                    all_new_updates.append(record.to_dict())

                db.session.commit()
                _jobs[job_id]["summary"].append({
                    "product": collector.product_name,
                    "total_found": len(updates),
                    "new_updates": new_count,
                    "updated_updates": updated_count,
                    "time_seconds": elapsed
                })
                _jobs[job_id]["progress"].append(
                    f"✓ {collector.product_name}: 发现 {len(updates)} 条，新增 {new_count} 条，覆盖更新 {updated_count} 条 ({elapsed}s)"
                )
            except Exception as e:
                db.session.rollback()
                _jobs[job_id]["summary"].append({"product": collector.product_name, "error": str(e)})
                _jobs[job_id]["progress"].append(f"❌ {collector.product_name}: {e}")

        # 飞书同步
        if all_new_updates:
            _jobs[job_id]["progress"].append("正在同步到飞书...")
            try:
                FeishuBitableSync().bulk_sync(all_new_updates[:50])
                _jobs[job_id]["progress"].append(f"✓ 飞书同步完成 ({len(all_new_updates[:50])} 条)")
            except Exception as e:
                _jobs[job_id]["progress"].append(f"❌ 飞书同步失败: {e}")

    total_time = round(time.time() - _jobs[job_id]["started_at"], 2)
    _jobs[job_id]["status"] = "done"
    _jobs[job_id]["total_time_seconds"] = total_time
    print(f"Collection job {job_id} done in {total_time}s")


@api_bp.route('/scan', methods=['POST'])
def trigger_scan():
    """启动后台采集任务，支持过滤参数"""
    from flask import current_app
    data = request.json or {}
    days = data.get('days')
    products = data.get('products') # Expecting a list of product names

    job_id = str(uuid.uuid4())[:8]
    app = current_app._get_current_object()
    # 使用 daemon=True 确保主线程退出时子线程也退出
    t = threading.Thread(target=_run_collection, args=(job_id, app, days, products), daemon=True)
    t.start()
    return jsonify({"status": "started", "job_id": job_id})


@api_bp.route('/scan/status/<job_id>', methods=['GET'])
def scan_status(job_id):
    """查询采集任务状态"""
    job = _jobs.get(job_id)
    if not job:
        # 如果内存中没有，可能是重启了，但为了体验返回 done
        return jsonify({"status": "unknown", "progress": ["任务不存在或已过期"]}), 404
    return jsonify(job)


@api_bp.route('/updates', methods=['GET'])
def get_updates():
    product = request.args.get('product')
    update_type = request.args.get('type')
    days = request.args.get('days', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = ProductUpdate.query

    if product:
        query = query.filter(ProductUpdate.product == product)
    if update_type:
        query = query.filter(ProductUpdate.update_type == update_type)

    if days:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(ProductUpdate.publish_time >= cutoff_date)
    elif start_date or end_date:
        if start_date:
            try:
                query = query.filter(ProductUpdate.publish_time >= datetime.strptime(start_date, '%Y-%m-%d'))
            except ValueError:
                pass
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
                query = query.filter(ProductUpdate.publish_time <= end)
            except ValueError:
                pass
    # 不传日期参数时返回全部数据

    updates = query.order_by(ProductUpdate.publish_time.desc()).limit(200).all()
    return jsonify([u.to_dict() for u in updates])


@api_bp.route('/updates/<update_id>', methods=['DELETE'])
def delete_update(update_id):
    """删除单条更新"""
    update = ProductUpdate.query.get(update_id)
    if not update:
        return jsonify({"error": "Update not found"}), 404
    
    try:
        db.session.delete(update)
        db.session.commit()
        return jsonify({"status": "success", "message": "Update deleted"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@api_bp.route('/updates/batch-delete', methods=['POST'])
def batch_delete_updates():
    """批量删除更新"""
    data = request.json or {}
    ids = data.get('ids', [])
    
    if not ids:
        return jsonify({"error": "No IDs provided"}), 400
    
    try:
        ProductUpdate.query.filter(ProductUpdate.id.in_(ids)).delete(synchronize_session=False)
        db.session.commit()
        return jsonify({"status": "success", "message": f"{len(ids)} updates deleted"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
