from ..repository.repository import CoffeeRepository,save_error_to_db
def error(function_name:str,file_name:str,error_msg:str):
    save_error_to_db(str(error_msg),function_name,file_name)