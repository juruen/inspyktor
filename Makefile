all: ui

ui:
	$(MAKE) -C $(CURDIR)/inspyktor/ui

clean:
	$(MAKE) -C $(CURDIR)/inspyktor/ui clean

