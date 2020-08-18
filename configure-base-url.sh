# This is what I used to configure the base URL in my containers

docker run --rm -it \
-v /opt/jetbrains/youtrack/conf:/opt/youtrack/conf \
jetbrains/youtrack:2020.3.4313 \
configure --base-url=https://youtrack.incplusplus.dev:443

docker run --rm -it \
-v /opt/jetbrains/hub/conf:/opt/hub/conf \
jetbrains/hub:2020.1.12375 \
configure --base-url=https://hub.incplusplus.dev:443

docker run --rm -it \
-v /opt/jetbrains/upsource/conf:/opt/upsource/conf \
jetbrains/upsource:2020.1.1802 \
configure --base-url=https://upsource.incplusplus.dev:443

docker run --rm -it \
-v /opt/jetbrains/teamcity/data:/data/teamcity_server/datadir \
jetbrains/teamcity-server:2020.1.3 \
configure --base-url=https://teamcity.incplusplus.dev:443