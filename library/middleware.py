class WorkspaceHeaders:
    def __init__(self,get_response):self.get_response=get_response
    def __call__(self,request):
        response=self.get_response(request)
        # UI uses only bundled assets; no third-party tracking, CDNs or inline scripts.
        response['Content-Security-Policy']="default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; form-action 'self'; img-src 'self' data:; font-src 'self'; script-src 'self'; style-src 'self'" + (" 'unsafe-inline'" if request.path.startswith('/admin/') else '')
        response['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
        if getattr(request,'user',None) and request.user.is_authenticated or request.path.startswith('/login/'):
            response['Cache-Control']='private, no-store'
        return response
