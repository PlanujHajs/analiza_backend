from fastapi import APIRouter, Depends
from typing import Dict, Any

from services.charts_service import ChartsService

router = APIRouter(prefix='/charts', tags=['charts'])


def get_charts_service() -> ChartsService:
    return ChartsService()


@router.get('/', response_description='Get all charts data')
async def get_charts(charts_service: ChartsService = Depends(get_charts_service)) -> Dict[str, Any]:
    return {
        'building_statistics': charts_service.get_building_statistics().to_dict(),
        'housing_prices': charts_service.get_housing_prices().to_dict(),
    }


@router.get('/building-statistics', response_description='Get building statistics data')
async def get_building_statistics(charts_service: ChartsService = Depends(get_charts_service)) -> Dict[str, Any]:
    return {'data': charts_service.get_building_statistics().to_dict()}


@router.get('/housing-prices', response_description='Get housing prices data')
async def get_housing_prices(charts_service: ChartsService = Depends(get_charts_service)) -> Dict[str, Any]:
    return {'data': charts_service.get_housing_prices().to_dict()}
