from datetime import datetime, timezone
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.receipt import GoodsReceipt
from app.repositories.order_repo import order_repo
from app.repositories.receipt_repo import receipt_repo
from app.schemas.receipt import GRCreateSchema


class GRService:
    async def create_goods_receipt(
        self,
        session: AsyncSession,
        received_by_id: UUID,
        gr_data: GRCreateSchema
    ) -> GoodsReceipt:
        # Verify PO exists
        po = await order_repo.get_by_id(session, gr_data.po_id)
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Purchase Order with ID '{gr_data.po_id}' not found."
            )

        # Build PO line items lookup map by item_name
        po_items_map = {
            item.get("item_name", "").lower(): item.get("quantity", 0)
            for item in po.line_items
        }

        has_discrepancy = False
        formatted_line_items = []

        for item in gr_data.line_items:
            expected_qty = po_items_map.get(item.item_name.lower())
            if expected_qty is None or item.quantity_received != expected_qty:
                has_discrepancy = True

            formatted_line_items.append({
                "item_name": item.item_name,
                "quantity_received": item.quantity_received,
                "condition_notes": item.condition_notes or "Good"
            })

        gr_status = "DISCREPANCY_FLAGGED" if has_discrepancy else "MATCHED"
        gr_number = await receipt_repo.generate_gr_number(session)
        now = datetime.now(timezone.utc)

        gr = GoodsReceipt(
            gr_number=gr_number,
            po_id=gr_data.po_id,
            received_by_id=received_by_id,
            delivery_note_ref=gr_data.delivery_note_ref,
            status=gr_status,
            line_items=formatted_line_items,
            received_at=now
        )

        # Update PO status accordingly
        po.status = "PARTIALLY_RECEIVED" if has_discrepancy else "FULLY_RECEIVED"

        created_gr = await receipt_repo.create(session, gr)
        return created_gr

    async def list_grs_for_po(self, session: AsyncSession, po_id: UUID) -> list[GoodsReceipt]:
        po = await order_repo.get_by_id(session, po_id)
        if not po:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Purchase Order with ID '{po_id}' not found."
            )
        return await receipt_repo.list_by_po(session, po_id)

    async def get_gr(self, session: AsyncSession, gr_id: UUID) -> GoodsReceipt:
        gr = await receipt_repo.get_by_id(session, gr_id)
        if not gr:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Goods Receipt with ID '{gr_id}' not found."
            )
        return gr


gr_service = GRService()
