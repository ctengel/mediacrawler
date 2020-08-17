
"""Simple tools for dealing with URL trees"""

class URL:
    """URL class"""
    # stringout
    def __init__(self, href, rel=None):
        self.href = href
        self.rel = rel
