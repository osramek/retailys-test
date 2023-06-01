import os

from flask import Flask, render_template, abort
from flask_caching import Cache
from flask_dramatiq import Dramatiq
from periodiq import PeriodiqMiddleware, cron

from importers.astra import AstraImporter


ONE_DAY_SECONDS = 24 * 60 * 60
CRON_EVERY_6_HOURS = "0 */6 * * *"

app = Flask(__name__)

app.config.update(
    DRAMATIQ_BROKER="dramatiq.brokers.redis:RedisBroker",
    DRAMATIQ_BROKER_URL=os.environ.get("DRAMATIQ_BROKER_URL"),
)

cache = Cache(
    config={
        "CACHE_TYPE": "RedisCache",
        "CACHE_REDIS_URL": os.environ.get("CACHE_REDIS_URL"),
    }
)
cache.init_app(app)

dramatiq = Dramatiq()
dramatiq.middleware.append(PeriodiqMiddleware())
dramatiq.init_app(app)


@dramatiq.actor(periodic=cron(CRON_EVERY_6_HOURS))
def import_products():
    import_result = AstraImporter().run()
    if import_result:
        AstraImportCache.store_all(import_result)


class AstraImportCache:
    @staticmethod
    def store_all(result):
        # We do not cache or persist the result itself at the moment.
        # For the current requirements purposes (and perf reasons) we just
        # prerender html snippets for all the tasks and store them in cache.
        AstraImportCache.store_task(1, f"Products cnt: {len(result.products)}")

        html = render_template("product_list.html", products=result.products)
        AstraImportCache.store_task(2, html)

        products_map = {p.code: p.name for p in result.products}
        html = render_template(
            "spare_parts.html", products=result.products, products_map=products_map
        )
        AstraImportCache.store_task(3, html)

    @staticmethod
    def store_task(task_num, data, timeout=ONE_DAY_SECONDS):
        cache.set(f"task_{task_num}", data, timeout=timeout)

    @staticmethod
    def get_task(task_num):
        res = cache.get(f"task_{task_num}")
        if res is None:
            # schedule the task in case of cache miss
            import_products.send()
        return res


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/tasks/<int:task_num>")
def task(task_num):
    if task_num < 1 or task_num > 3:
        abort(404)
    result = AstraImportCache.get_task(task_num)
    return render_template("task.html", task_num=task_num, result=result)
