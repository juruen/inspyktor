all: ui

ui:
	$(MAKE) -C $(CURDIR)/inspyktor/ui

clean:
	$(MAKE) -C $(CURDIR)/inspyktor/ui clean

pep8:
	pep8 --repeat --exclude=ui .
