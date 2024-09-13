def remove_empty_lines(get_response):
    def middleware(request):
        response = get_response(request)
        if 'html' in response.headers['Content-Type']:
            response.content = b'\n'.join(ln for ln in response.content.splitlines() if ln.strip())
        return response
    return middleware
