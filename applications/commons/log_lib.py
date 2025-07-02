
from rest_framework.response import Response
from rest_framework import status


class APIResponse(object):
    def __init__(self, **kwargs):
        self.code_status = 0
        self.message = ""
        self.errors = {}
        self.data_resp = {}
        self.kwargs = {}

    def check_message(self, message):
        self.message = self.message if self.message else message

    def check_code(self, code_status):
        self.code_status = self.code_status if self.code_status else code_status

    def add_errors(self, error):
        if isinstance(error, list):
            self.errors.append(error)
        else:
            self.errors.update(error)

    def get_code(self, code=1200):
        return self.code_status if self.code_status else code
    
    def make_format(self):
        if self.errors:
            code_status = self.get_code(1400)
            message = self.message
            result = False
        else:
            code_status = self.get_code(1200)
            message = self.message if self.message else 'Success'
            result = True
        return dict(result=result, message=message, status_code=code_status, data=self.data_resp, error=self.errors, **self.kwargs)
    
    
def trace_api(class_response=APIResponse):
    def decorator(func):
        def inner(request, **kwargs):
            _response = class_response(api_func=func.__name__)
            kwargs.update(request=request, _response=_response)
            
            try:
                func(**kwargs)
            except Exception as e:
                print (e)
                
            return Response(_response.make_format(),  status=status.HTTP_200_OK)

        return inner
    
    return decorator

        