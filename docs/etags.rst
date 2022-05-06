ETags
-----

ETags are used in to check whether pages need to be re-calculated or can be served from cache.
An ETag is simply a string. Under ``plone.app.caching``, it is a string of tokens separated by pipe characters.
The tokens hold values such as a user id, the current skin name, or a counter indicating how many objects have been added to the site.
The idea is that the browser sends a request with the ETag included in an ``If-None-Match`` header.
Plone can then quickly calculate the current ETag for the requested resource.
If the ETag is the same, Plone can reply with ``304 NOT MODIFIED`` response, telling the browser to use its cached copy.
Otherwise, Plone renders the page and returns it as normal.

Many caching operations use ETags. The tokens to include are typically listed in an ``etags`` tuple in the operation's options.

The ETag names tokens supported by default are:

userid
    The current user's id

roles
    A list of the current user's roles in the given context

language
    The language(s) accepted by the browser, in the ``ACCEPT_LANGUAGE`` header

userLanguage
    The current user's preferred language

lastModified
    A timestamp indicating the last-modified date of the given context

catalogCounter
    A counter that is incremented each time the catalog is updated.
    I.e. each time content in the site is changed.

locked
    Whether or not the given context is locked for editing.

skin
    The name of the current skin (theme)

resourceRegistries
    A timestamp indicating the last-modified timestamp for the Resource Registries.
    This is useful for avoiding requests for expired resources from cached pages.

It is possible to provide additional tokens by registering an ``IETagValue`` adapter.
This should be a named adapter on the published object (typically a view, file resource or Zope page template object) and request, with a unique name.
The name is used to look up the component. Thus, you can also override one of the tokens above for a particular type of context or request (e.g. via a browser layer), by registering a more specific adapter with the same name.

As an example, here is the ``language`` adapter::

    from plone.app.caching.interfaces import IETagValue
    from zope.component import adapter
    from zope.interface import implementer
    from zope.interface import Interface

    @implementer(IETagValue)
    @adapter(Interface, Interface)
    class Language(object):
        """The ``language`` etag component, returning the value of the
        HTTP_ACCEPT_LANGUAGE request key.
        """

        def __init__(self, published, request):
            self.published = published
            self.request = request

        def __call__(self):
            return self.request.get('HTTP_ACCEPT_LANGUAGE', '')

This is registered in ZCML like so::

    <adapter factory=".etags.Language" name="language" />
