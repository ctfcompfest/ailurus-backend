from ailurus.utils.config import get_app_config
from ailurus.utils.security import validteam_only
from flask import Blueprint, jsonify
from mdx_gfm import GithubFlavoredMarkdownExtension

import markdown
import os

public_docs_blueprint = Blueprint("public_docs_blueprint", __name__, url_prefix="/docs")
public_docs_blueprint.before_request(validteam_only)

@public_docs_blueprint.get("/<string:page>/")
def get_docs(page):
    base_path = os.path.join(get_app_config("TEMPLATE_DIR"), "docs")
    ALLOWED_PAGE = [elm.replace(".md", "") for elm in os.listdir(base_path)]
    if page not in ALLOWED_PAGE:
        return jsonify(status="not found.", message="page not found."), 404
    with open(os.path.join(base_path, page + ".md")) as f:
        content = f.read()
    response = markdown.markdown(content, extensions=[GithubFlavoredMarkdownExtension()])
    return jsonify(status="success", data=response)