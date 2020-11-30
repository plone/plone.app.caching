Support for *plone.restapi*.
Define `cache:ruleset` assignments for anonymous accessible endpoints.
Attention: Relies on *Vary* header unless *plone.restapi* gives up content negotation.
Latter may conflict with edge side cache not supporting the Vary header.
[jensens]