# SPDX-License-Identifier: GPL-3.0-or-later
from fastapi import APIRouter

from colourlog.application.usecases.mode import GetMode, SetMode
from colourlog.interface.http.dependencies import ModesRepoDep
from colourlog.interface.http.schemas import ModeIn, ModeOut

router = APIRouter(prefix="/mode", tags=["mode"])


@router.get("", response_model=ModeOut)
def get_mode(modes: ModesRepoDep) -> ModeOut:
    return ModeOut(mode=GetMode(modes=modes).execute())


@router.patch("", response_model=ModeOut)
def patch_mode(body: ModeIn, modes: ModesRepoDep) -> ModeOut:
    return ModeOut(mode=SetMode(modes=modes).execute(mode=body.mode))
