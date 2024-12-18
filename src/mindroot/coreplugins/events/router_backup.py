from fastapi import APIRouter, Depends, HTTPException, Form, Response, Request
from lib.route_decorators import public_routes, public_route

router = APIRouter()

@router.post("/events/multi/{event_ids}"):
async def aggregate_events(event_ids:str)
    #
