from fastapi import APIRouter, Depends, HTTPException, Body, Query
from app.schemas.company import Company, Payment
from app.schemas.collections import PricingData
from app.services.company_service import CompanyService
from app.api.deps import get_company_service

router = APIRouter()

@router.get("/", response_model=Company)
async def get_company_details(
    owner: str = Query(...),
    company_service: CompanyService = Depends(get_company_service)
):
    return await company_service.get_company_details(owner)

@router.post("/details/", response_model=Company)
async def update_company_details(
    owner: str = Query(...),
    company_data: Company = Body(...),
    company_service: CompanyService = Depends(get_company_service)
):
    return await company_service.update_company_details(owner, company_data)

@router.get("/payment-details/", response_model=Payment)
async def get_payment_details(
    owner: str = Query(...),
    company_service: CompanyService = Depends(get_company_service)
):
    return await company_service.get_payment_details(owner)

@router.post("/payment-details/", response_model=Payment)
async def update_payment_details(
    owner: str = Query(...),
    payment_data: Payment = Body(...),
    company_service: CompanyService = Depends(get_company_service)
):
    return await company_service.update_payment_details(owner, payment_data)

@router.get("/pricing/", response_model=PricingData)
async def get_pricing_data(
    owner: str = Query(...),
    pricing_service: CompanyService = Depends(get_company_service)
):
    return await pricing_service.get_pricing_data(owner)

@router.post("/pricing/", response_model=PricingData)
async def update_pricing_data(
    owner: str = Query(...),
    pricing_data: PricingData = Body(...),
    pricing_service: CompanyService = Depends(get_company_service)
):
    return await pricing_service.update_pricing_data(owner, pricing_data)