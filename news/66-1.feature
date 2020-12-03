Introduce *terseCaching* operation and `plone.content.dynamic` ruleset.
*terseCaching* is a rule with by default 10s in browser cache and 60s in edge cache.
It is intended to be used for highly dynamic content defined in the `plone.content.dynamic` ruleset.
The combination reduces load on the backend if there a lots of requests.
[jensens]
