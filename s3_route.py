from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from .s3_services import S3Service

router = APIRouter(tags=["S3"])
s3_service = S3Service()


@router.get("/presigned-url")
async def get_presigned_url(
    filename: str = Query(..., description="Tên file"),
    contentType: str = Query(..., alias="contentType", description="Content type của file")
):
    try:
        result = await s3_service.generate_presigned_url(filename, contentType)
        
        return {
            "putUrl": result["putUrl"],  
            "url": f"{result['fileKey']}"  
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{file_key}")
async def get_file(file_key: str):
    print(f"Accessing file: {file_key}")
    
    try:
        get_url = await s3_service.generate_presigned_get_url(
            file_key, 
            expires_in_seconds=604800  # 7 ngày
        )
        
        print(f"Redirecting to: {get_url}")
        
        # Redirect đến URL của S3
        return RedirectResponse(url=get_url)
        
    except Exception as e:
        print(f"Lỗi khi lấy file: {e}")
        raise HTTPException(status_code=404, detail="Không tìm thấy file")