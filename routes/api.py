from flask import Blueprint, jsonify, request
from models import db, ProductUpdate, CompetitiveLandscape
from collectors.changelog_scrapers import (
    PostHogChangelogCollector,
    MixpanelChangelogCollector,
    AmplitudeChangelogCollector
)
from collectors.playwright_scrapers import SensorsDataCollector
from services.feishu_sync import FeishuBitableSync
from datetime import datetime, timedelta
import threading
import uuid
import time

api_bp = Blueprint('api', __name__)

# 存储后台任务状态
_jobs = {}


def _run_collection(job_id, app):
    """后台线程执行采集任务"""
    _jobs[job_id] = {"status": "running", "progress": [], "summary": [], "started_at": time.time()}

    collectors = [
        PostHogChangelogCollector(),
        MixpanelChangelogCollector(),
        AmplitudeChangelogCollector(),
        SensorsDataCollector(),
    ]

    all_new_updates = []

    with app.app_context():
        for collector in collectors:
            _jobs[job_id]["progress"].append(f"正在采集 {collector.product_name}...")
            try:
                t0 = time.time()
                updates = collector.collect()
                elapsed = round(time.time() - t0, 2)

                new_count = 0
                for u in updates:
                    exists = (
                        ProductUpdate.query.filter_by(content_hash=u['content_hash']).first() or
                        ProductUpdate.query.filter_by(source_url=u['source_url']).first()
                    )
                    if not exists:
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
                        db.session.flush()
                        all_new_updates.append(record.to_dict())
                        new_count += 1

                db.session.commit()
                _jobs[job_id]["summary"].append({
                    "product": collector.product_name,
                    "total_found": len(updates),
                    "new_updates": new_count,
                    "time_seconds": elapsed
                })
                _jobs[job_id]["progress"].append(
                    f"✓ {collector.product_name}: 发现 {len(updates)} 条，新增 {new_count} 条 ({elapsed}s)"
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


@api_bp.route('/collect', methods=['POST'])
def trigger_collect():
    """启动后台采集任务，立即返回 job_id"""
    from flask import current_app
    job_id = str(uuid.uuid4())[:8]
    app = current_app._get_current_object()
    t = threading.Thread(target=_run_collection, args=(job_id, app), daemon=True)
    t.start()
    return jsonify({"status": "started", "job_id": job_id})


@api_bp.route('/collect/status/<job_id>', methods=['GET'])
def collect_status(job_id):
    """查询采集任务状态"""
    job = _jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
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
