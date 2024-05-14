build:
	@echo "Nothing to build. Only install. Destination is: " $(DESTDIR)

install:
	mkdir -p $(DESTDIR)/var/lib/Base
	install Base/*.py $(DESTDIR)/var/lib/Base
	mkdir -p $(DESTDIR)/usr/bin
	ln -s $(DESTDIR)/var/lib/Base/__init__.py $(DESTDIR)/usr/bin/Base
	ln -s $(DESTDIR)/var/lib/Base/stats.py $(DESTDIR)/usr/bin/Baseview
