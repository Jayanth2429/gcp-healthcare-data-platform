.PHONY: test resolve snapshot terraform-check

test:
	python -m pytest -q

resolve:
	python -m scripts.resolve_cms_resource

snapshot:
	python -m scripts.download_cms_snapshot

terraform-check:
	cd terraform && terraform fmt -check && terraform init -backend=false && terraform validate
