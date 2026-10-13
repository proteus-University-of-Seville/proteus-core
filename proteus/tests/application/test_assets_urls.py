# ==========================================================================
# File: test_assets_urls.py
# Description: tests of the replacement of the dummy assets URLs of the HTML
# ==========================================================================

from proteus.application import replace_assets_urls


def test_assets_urls_of_attributes_are_replaced():
    html = '<img src="assets:///a.png"/><img alt="x" src="assets:///b%20c.png"/>'

    assert replace_assets_urls(html, "file:///p/assets/") == (
        '<img src="file:///p/assets/a.png"/><img alt="x" src="file:///p/assets/b%20c.png"/>'
    )


def test_assets_urls_in_the_text_are_kept():
    # E.g. a comment that explains the syntax of an image in Markdown
    html = '<p>Use <code>![text](assets:///file.png)</code> or assets:///file.png</p><img src="assets:///file.png"/>'

    assert replace_assets_urls(html, "./assets/") == (
        '<p>Use <code>![text](assets:///file.png)</code> or assets:///file.png</p><img src="./assets/file.png"/>'
    )
