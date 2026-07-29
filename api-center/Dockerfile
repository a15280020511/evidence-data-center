FROM krakend:2.13.8@sha256:397680d16a0a44156d5bc47955385f2f109a3cf8b66f47bfe5db32d446c9effe

COPY krakend.tmpl /etc/krakend/krakend.tmpl
COPY krakend.validation.json /etc/krakend/krakend.validation.json

RUN krakend check -tnc /etc/krakend/krakend.validation.json \
    && rm /etc/krakend/krakend.validation.json

ENV FC_ENABLE=1
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget --spider --quiet http://127.0.0.1:8080/__health || exit 1

CMD ["run", "-c", "/etc/krakend/krakend.tmpl"]
