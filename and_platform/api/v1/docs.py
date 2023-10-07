from and_platform.cache import cache
from and_platform.core.config import get_app_config
from flask import Blueprint, jsonify, request
import markdown
import os
from mdx_gfm import GithubFlavoredMarkdownExtension

public_docs_blueprint = Blueprint("public_docs_blueprint", __name__, url_prefix="/docs")

@public_docs_blueprint.get("/<string:page>")
# @cache.cached()
def get_docs(page):
    base_path = os.path.join(get_app_config("TEMPLATE_DIR"), "docs")
    ALLOWED_PAGE = [elm.replace(".md", "") for elm in os.listdir(base_path)]
    if page not in ALLOWED_PAGE:
        return jsonify(status="not found.", message="not found."), 404
    with open(os.path.join(base_path, page + ".md")) as f:
        content = f.read()
    response = markdown.markdown(content, extensions=[GithubFlavoredMarkdownExtension()])
    return jsonify(status="success", data=response)