== curl ==
# curl -F "file=@drive1.asc" -F "format=asc" http://127.0.0.1:5000/api/logs
# curl -F "file=@vehicle.dbc" http://127.0.0.1:5000/api/logs/1/dbc
# GET  /api/logs/1/messages?filter=0x123
# GET  /api/logs/1/signals/RPM
# GET  /api/logs/1/export   (CSV)

== session plan ==
# Session 1: parser (asc/csv fixtures) → tests
# Session 2: dbc decode (bit math) + signals → tests
# Session 3: api + web charts + replay → screenshots → README → CI/Docker/Pages → tag
