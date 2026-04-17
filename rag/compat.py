"""Patch llama_index QdrantVectorStore for Python 3.14 + Pydantic v2 compatibility.

On Python 3.14, Pydantic v2's __setattr__ for PrivateAttr fields is broken —
assignments like self._client = value in __init__ silently fail to persist.
This patch wraps __init__ to force values directly into __pydantic_private__.
"""
import llama_index.vector_stores.qdrant.base as _mod

_OrigCls = _mod.QdrantVectorStore
_OrigInit = _OrigCls.__init__


def _patched_init(self, *args, **kwargs):
    """Call original __init__, then force private attrs into pydantic storage."""
    # Capture all args that __init__ will try to store
    import inspect
    sig = inspect.signature(_OrigInit)
    bound = sig.bind(self, *args, **kwargs)
    bound.apply_defaults()

    # Run original init
    _OrigInit(self, *args, **kwargs)

    # Force the critical private attrs into __pydantic_private__
    priv = self.__pydantic_private__
    if priv is None:
        object.__setattr__(self, "__pydantic_private__", {})
        priv = self.__pydantic_private__

    # Get values from bound args that __init__ would have stored
    client = bound.arguments.get("client")
    aclient = bound.arguments.get("aclient")

    if client is not None:
        priv["_client"] = client
        priv["_collection_initialized"] = _OrigCls._collection_exists(self, self.collection_name)
    elif aclient is not None:
        priv["_aclient"] = aclient
        priv["_collection_initialized"] = False
    else:
        # URL-based init: client was created inside __init__
        # We can't easily get it, so try reading from the object
        pass

    # Handle hybrid search functions
    enable_hybrid = bound.arguments.get("enable_hybrid", False)
    if enable_hybrid:
        sparse_doc_fn = bound.arguments.get("sparse_doc_fn")
        sparse_query_fn = bound.arguments.get("sparse_query_fn")
        hybrid_fusion_fn = bound.arguments.get("hybrid_fusion_fn")
        if sparse_doc_fn:
            priv["_sparse_doc_fn"] = sparse_doc_fn
        if sparse_query_fn:
            priv["_sparse_query_fn"] = sparse_query_fn
        if hybrid_fusion_fn:
            priv["_hybrid_fusion_fn"] = hybrid_fusion_fn


_OrigCls.__init__ = _patched_init
