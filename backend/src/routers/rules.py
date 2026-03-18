from fastapi import APIRouter, HTTPException
from typing import List
from beanie import PydanticObjectId

from ..models import Rule

router = APIRouter(prefix="/api/rules", tags=["rules"])

@router.get("", response_model=List[Rule])
async def get_rules():
    rules = await Rule.find_all().to_list()
    return rules

@router.post("", response_model=Rule)
async def create_rule(rule: Rule):
    await rule.insert()
    return rule

@router.put("/{rule_id}", response_model=Rule)
async def update_rule(rule_id: str, updated_data: Rule):
    rule = await Rule.get(PydanticObjectId(rule_id))
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    await rule.set({
        Rule.name: updated_data.name,
        Rule.description: updated_data.description,
        Rule.condition_field: updated_data.condition_field,
        Rule.condition_operator: updated_data.condition_operator,
        Rule.condition_value: updated_data.condition_value,
        Rule.action: updated_data.action,
        Rule.action_value: updated_data.action_value,
        Rule.enabled: updated_data.enabled,
    })

    return rule

@router.delete("/{rule_id}")
async def delete_rule(rule_id: str):
    rule = await Rule.get(PydanticObjectId(rule_id))
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    await rule.delete()
    return {"message": "Deleted successfully"}
