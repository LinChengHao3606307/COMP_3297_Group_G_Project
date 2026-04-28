source ../venv/bin/activate

pkill -f gunicorn

DJANGO_SETTINGS_MODULE=betatrax.settings_production \
gunicorn --bind 0.0.0.0:8000 --workers 2 --threads 2 --worker-class gthread --max-requests 1000 --max-requests-jitter 100 --preload --log-level info betatrax.wsgi:application

#[Unit]
#Description=COMP3297 Betatrax Application
#After=network.target postgresql.service
#Wants=network.target postgresql.service

#[Service]
#Type=simple
#User=ubuntu
#Group=www-data

#WorkingDirectory=~COMP_3297_Group_G_Project/src

#Environment="DJANGO_SETTINGS_MODULE=betatrax.settings_production"
#Environment="PATH=~/COMP_3297_Group_G_Project/venv/bin"

#ExecStart=~/COMP_3297_Group_G_Project/venv/bin/gunicorn \
#    --bind 0.0.0.0:8000 \
#    --workers 2 \
#    --threads 2 \
#    --worker-class gthread \
#    --max-requests 1000 \
#    --max-requests-jitter 100 \
#    --preload \
#    --log-level info \
#    betatrax.wsgi:application

#Restart=always
#RestartSec=5

#StandardOutput=journal
#StandardError=journal

#[Install]
#WantedBy=multi-user.target