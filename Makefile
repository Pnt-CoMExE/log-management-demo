.PHONY: up down logs seed-alert test backend-install frontend-install saas-certs

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

saas-certs:
	bash scripts/gen_self_signed_cert.sh

saas-up:
	docker compose --profile saas up --build -d

test:
	cd backend && python -m pytest ../tests -q

backend-install:
	cd backend && pip install -r requirements.txt

frontend-install:
	cd frontend && npm install
