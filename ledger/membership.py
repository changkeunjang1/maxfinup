# -*- coding: utf-8 -*-
"""회원 전용 메뉴(자산관리 · 인생 후반전 · 인생 후반전1) 열람 권한.

가입은 누구나 할 수 있지만, 관리자가 승인(MEMBER_GROUP에 추가)해야 본문을 읽을 수 있다.
관리자(staff)는 항상 열람할 수 있다.
"""

MEMBER_GROUP = "회원 열람 승인"


def access_level(user):
    """'member'(승인 회원) · 'pending'(가입했지만 승인 전) · 'guest'(로그인 안 함)."""
    if not user.is_authenticated:
        return "guest"
    if user.is_staff or user.groups.filter(name=MEMBER_GROUP).exists():
        return "member"
    return "pending"
