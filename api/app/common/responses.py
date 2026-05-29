def success_payload(message: str = "Operação bem sucedida!", data=None, status: int = 200):
    return {"success": True, "message": message, "data": data}, status


def error_payload(message: str, status: int = 400, errors=None):
    return {"success": False, "message": message, "errors": errors}, status
