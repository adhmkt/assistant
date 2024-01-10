class ProductionConfig:
    import os
    EBUG = False
    REDIS_TLS_URL = os.environ.get('REDIS_TLS_URL')
    REDIS_URL = os.environ.get('REDIS_URL')
