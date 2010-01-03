

class ControlPanel(object):
    """Control panel view
    """
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
    
    def __call__(self):
        return self.index()
