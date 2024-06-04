from fastapi import APIRouter

router = APIRouter()

@router.get('/commands')
def list_commands():
    commands = ['say', 'json_encoded_md', 'pic_of_me', 'read', 'write', 'dir', 'cd']
    return {'commands': commands}