from fastapi import APIRouter,Request,Response,HTTPException
from ..models.model import APIResponse,UserRequest
from pydantic import ValidationError
import json 
from datetime import datetime,UTC
from ..services.service import GraphService
router=APIRouter(prefix="/codeApp/api/v1",tags=["Code"])


@router.post("/chat_With_agent",response_model=APIResponse)
async def code_with_agent(request:Request,response:Response):
        service=GraphService()
        try:
            raw_data =await request.json()
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON Format")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid request body")
        
        if not raw_data:
             return APIResponse(
                  code=400,
                  status="error",
                  message="Request body cannot be empty",
                  error={"details":"Empty body"},
                  timestamp=datetime.now(UTC).isoformat()
             )
        
        try:
             validated_data=UserRequest(**raw_data)
        except ValidationError as e:
            return APIResponse(
                code=400,
                status="error",
                message="Validation failed",
                error={"details": e.errors()[0]["msg"]},
                timestamp=datetime.now(UTC).isoformat()
            )
        
        try:
             result=await service.build_graph(validated_data.customer_id,validated_data.user_query)
             response.status_code=result.code
             return result
        except Exception as e:
            return APIResponse(
                code=500,
                status="failed",
                message="Bot processing failed",
                error={"details": str(e)},
                timestamp=datetime.now(UTC).isoformat()
            )

