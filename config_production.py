class ProductionConfig:
    DEBUG = False
    REDIS_TLS_URL =  "rediss://:pb832bd232f647cd9d6f05ebf87d850310ef9d4c76c6bcdadebd0b91838b0987d@ec2-44-199-142-192.compute-1.amazonaws.com:6380"
    REDIS_URL = "redis://:pb832bd232f647cd9d6f05ebf87d850310ef9d4c76c6bcdadebd0b91838b0987d@ec2-44-199-142-192.compute-1.amazonaws.com:6379"
    # ... other production-specific settings ...
