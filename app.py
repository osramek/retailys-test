import os
from flask import Flask, render_template, abort
from flask_caching import Cache
from flask_dramatiq import Dramatiq
from periodiq import PeriodiqMiddleware, cron


from importers.astra import AstraImporter

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


@dramatiq.actor(periodic=cron("0 6,22 * * *"))
def import_products():
    result = AstraImporter().run()
    if result:
        # Note we do not cache/persist the result itself.
        # ATM we just prerender html snippets for
        AstraImportCache.prerender_and_store_all(result)


class AstraImportCache:
    @staticmethod
    def store(task_num, rendered_html, timeout=24 * 60 * 60):
        cache.set(f"task_{task_num}", rendered_html, timeout=timeout)

    @staticmethod
    def get(task_num):
        return cache.get(f"task_{task_num}")

    @staticmethod
    def prerender_and_store_all(result):
        AstraImportCache.store(1, f"Products cnt: {len(result.products)}")

        html = render_template("product_list.html", products=result.products)
        AstraImportCache.store(2, html)

        products_map = {p.code: p.name for p in result.products}
        html = render_template(
            "spare_parts.html", products=result.products, products_map=products_map
        )
        AstraImportCache.store(3, html)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/tasks/<int:task_num>")
def task(task_num):
    if task_num < 1 or task_num > 3:
        abort(404)
    result = AstraImportCache.get(task_num)
    return render_template("task.html", task_num=task_num, result=result)


import_products.send()
