import logging

import boto3
import watchtower


class AWSSettings:
    access_key_id: str
    secret_access_key: str
    region: str


LOG_GROUP_NAME = "log-group-name"
STREAM_NAME = "log-stream"


config = AWSSettings()

cloudwatch_logger = logging.getLogger("cloudwatch_log")
cloudwatch_logger.setLevel(logging.INFO)
cloudwatch_logger.addHandler(
    watchtower.CloudWatchLogHandler(
        log_group=LOG_GROUP_NAME,
        stream_name=STREAM_NAME,
        boto3_client=boto3.client(
            "logs",
            aws_access_key_id=config.access_key_id,
            aws_secret_access_key=config.secret_access_key,
            region_name=config.region,
        ),
        send_interval=1,  # 미설정 시 60초마다 전송
        use_queues=False,  # 비동기에서 사용 시 False로 안 하면 이벤트 루프를 못 찾음
    )
)
