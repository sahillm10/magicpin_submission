#!/usr/bin/env python3
"""
magicpin AI Challenge — Conversation Handlers
=============================================
Multi-turn conversational tiebreaker module specified in challenge-brief.md §7.4.
Implements stateful dialogue transition handling:
- Auto-reply / canned response detection -> graceful exit
- Explicit commitment detection -> immediate action mode
- Hostility / opt-out -> polite cessation
- Out-of-scope redirection
"""

from typing import Dict, Any
from bot import ReplyEngine, ReplyRequest


def respond(state: Dict[str, Any], merchant_message: str) -> Dict[str, Any]:
    """
    Given the conversation so far + the merchant's latest message, produce the reply.

    Inputs:
        state: dict containing conversation state
               (conversation_id, merchant_id, customer_id, turn_number, etc.)
        merchant_message: latest message received from merchant or customer

    Returns:
        dict with:
            action: "send" | "wait" | "end"
            body: str (if action == "send")
            cta: str (if action == "send")
            rationale: str
    """
    conv_id = state.get("conversation_id", "conv_default")
    merchant_id = state.get("merchant_id")
    customer_id = state.get("customer_id")
    turn = state.get("turn_number", state.get("turn", 2))
    from_role = state.get("from_role", "merchant")
    received_at = state.get("received_at", "2026-04-26T12:00:00Z")

    req = ReplyRequest(
        conversation_id=conv_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        from_role=from_role,
        message=merchant_message,
        received_at=received_at,
        turn_number=turn
    )

    return ReplyEngine.handle_reply(req)
