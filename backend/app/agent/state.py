from typing import TypedDict, Annotated, Sequence, Optional, Dict, Any, List, Literal
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field, ConfigDict

# ==============================================================================
# 1. Stage & Progress Types
# ==============================================================================
StageStatus = Literal["pending", "in_progress", "complete", "blocked"]
RecommendationStatus = Literal["none", "pending_review", "accepted", "modified", "rejected"]

class RequestProgress(BaseModel):
    clarification: StageStatus = Field(default="pending", description="Status tahap klarifikasi kebutuhan")
    demand_analysis: StageStatus = Field(default="pending", description="Status tahap analisis stok & aset")
    validation: StageStatus = Field(default="pending", description="Status tahap validasi & review rekomendasi")
    ready_for_submission: StageStatus = Field(default="pending", description="Status kesiapan submit PR")

    model_config = ConfigDict(extra="ignore")


# ==============================================================================
# 2. Live PR Artifact & Specifications
# ==============================================================================
class PRSpecification(BaseModel):
    field_name: str = Field(..., description="Nama field spesifikasi, e.g. RAM, GPU, OS")
    value: Optional[str] = Field(default=None, description="Nilai spesifikasi teknis")
    is_confirmed: bool = Field(default=False, description="True jika sudah dikonfirmasi user / eksplisit tanpa ambiguitas")

    model_config = ConfigDict(extra="ignore")


def update_specification(
    existing: PRSpecification, 
    new_value: Optional[str], 
    new_is_confirmed: Optional[bool] = None
) -> PRSpecification:
    """
    Memperbarui nilai spesifikasi dengan aturan reset:
    - Jika new_is_confirmed diberikan secara eksplisit, gunakan nilai tersebut.
    - Jika value berubah dan sebelumnya sudah confirmed (dan new_is_confirmed tidak eksplisit),
      reset is_confirmed menjadi False (butuh re-konfirmasi).
    - Jika value tidak berubah, pertahankan nilai is_confirmed sebelumnya.
    """
    if new_is_confirmed is not None:
        confirmed = new_is_confirmed
    elif existing.value != new_value and existing.is_confirmed:
        confirmed = False
    else:
        confirmed = existing.is_confirmed

    return existing.model_copy(update={"value": new_value, "is_confirmed": confirmed})


class PRArtifact(BaseModel):
    pr_number: Optional[str] = Field(default=None, description="Nomor Purchase Requisition resmi")
    item_name: Optional[str] = Field(default=None, description="Nama barang/kategori utama")
    category: Optional[str] = Field(default=None, description="Kategori pengadaan")
    quantity: Optional[int] = Field(default=None, description="Kuantitas final barang")
    department: Optional[str] = Field(default=None, description="ID Departemen pemohon")
    cost_center: Optional[str] = Field(default=None, description="Cost Center pemohon")
    purpose: Optional[str] = Field(default=None, description="Tujuan/justifikasi bisnis")
    required_date: Optional[str] = Field(default=None, description="Target tanggal kebutuhan (YYYY-MM-DD)")
    specifications: List[PRSpecification] = Field(default_factory=list, description="Daftar spesifikasi teknis item")
    status: str = Field(default="draft", description="Status dokumen PR (draft/submitted/approved)")
    is_ready_for_confirmation: bool = Field(
        default=False,
        description="True jika seluruh field wajib (item, quantity, purpose, required_date) telah terisi dan siap dikonfirmasi oleh user"
    )

    model_config = ConfigDict(extra="ignore")


# ==============================================================================
# 3. Demand Analysis Breakdown
# ==============================================================================
class DemandBreakdown(BaseModel):
    requested_qty: int = Field(..., description="Kuantitas awal yang diminta user")
    existing_inventory: int = Field(default=0, description="Stok gudang yang tersedia")
    assignable_assets: int = Field(default=0, description="Aset idle yang dapat direalokasikan")
    reserved_qty: int = Field(default=0, description="Kuantitas yang sudah di-reserve")
    net_new_purchase: int = Field(..., description="Jumlah rekomendasi pembelian baru")
    estimated_saving: Optional[float] = Field(default=None, description="Estimasi penghematan biaya dari stok/aset")
    is_manually_overridden: bool = Field(default=False, description="True jika net_new_purchase di-override manual oleh user")
    override_reason: Optional[str] = Field(default=None, description="Alasan manual adjustment dari user")

    model_config = ConfigDict(extra="ignore")


# ==============================================================================
# 4. Human-Readable AI Activity
# ==============================================================================
class AgentAction(BaseModel):
    tool_name: str = Field(..., description="Nama deterministic mock tool yang dieksekusi")
    label: str = Field(..., description="Label human-readable singkat, misal: 'Checking warehouse inventory'")
    status: Literal["running", "done", "failed"] = Field(default="done")
    result_summary: Optional[str] = Field(default=None, description="Ringkasan hasil, misal: '4 units available in stock'")

    model_config = ConfigDict(extra="ignore")


# ==============================================================================
# 5. Attention / Exception Items
# ==============================================================================
class AttentionItem(BaseModel):
    id: str = Field(..., description="ID deterministik: spec_{field_name}, budget_{cost_center}, policy_{rule_key}, override_stale_{cost_center}")
    category: Literal["specification", "budget", "policy"] = Field(..., description="Kategori isu")
    severity: Literal["warning", "blocking"] = Field(..., description="Tingkat urgensi isu")
    message: str = Field(..., description="Pesan deskriptif issue/rekomendasi")
    resolved: bool = Field(default=False, description="Status apakah item sudah di-resolve/dismiss")

    model_config = ConfigDict(extra="ignore")


# ==============================================================================
# 6. Legacy Schemas (DEPRECATED - Kept for Backward Compatibility)
# ==============================================================================
class RequirementDraftSchema(BaseModel):
    """DEPRECATED: Legacy requirement schema. Use PRArtifact instead."""
    category: Optional[str] = None
    item: Optional[str] = None
    quantity: Optional[int] = None
    purpose: Optional[str] = None
    required_date: Optional[str] = None
    specifications: Dict[str, Any] = Field(default_factory=dict)
    is_complete: bool = False
    model_config = ConfigDict(extra="ignore")


class DemandAnalysisSchema(BaseModel):
    """DEPRECATED: Legacy demand schema. Use DemandBreakdown instead."""
    requested_quantity: Optional[int] = None
    available_inventory: int = 0
    available_assets: int = 0
    recommended_quantity: Optional[int] = None
    justification: Optional[str] = None
    is_complete: bool = False
    model_config = ConfigDict(extra="ignore")


class PRDraftSchema(BaseModel):
    """DEPRECATED: Legacy PR draft schema. Use PRArtifact instead."""
    pr_number: str = ""
    category: str = ""
    item: str = ""
    quantity: int = 1
    specifications: Dict[str, Any] = Field(default_factory=dict)
    purpose: str = ""
    required_date: str = ""
    business_justification: str = ""
    demand_analysis_summary: str = ""
    model_config = ConfigDict(extra="ignore")


# ==============================================================================
# 7. LangGraph Annotated Reducers
# ==============================================================================

def reduce_attention_items(
    existing: Optional[List[Dict[str, Any]]], 
    incoming: Optional[List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """
    Reducer untuk AttentionItem:
    - Upsert berdasarkan ID deterministik (spec_{field}, budget_{cost_center}, policy_{rule}, override_stale_{cost_center}).
    - Menjaga item lama jika sudah ditandai resolved: True oleh user (tidak ditimpa).
    """
    if not existing:
        return incoming or []
    if not incoming:
        return existing

    items_by_id = {item["id"]: item for item in existing}
    for new_item in incoming:
        old_item = items_by_id.get(new_item["id"])
        if old_item and old_item.get("resolved") is True:
            continue
        items_by_id[new_item["id"]] = new_item
    return list(items_by_id.values())


def reduce_agent_activity(
    existing: Optional[List[Dict[str, Any]]], 
    incoming: Optional[List[Dict[str, Any]]]
) -> List[Dict[str, Any]]:
    """Reducer untuk AgentActivity: Append ke list riwayat aktivitas tool."""
    if not existing:
        return incoming or []
    if not incoming:
        return existing
    return list(existing) + list(incoming)


def reduce_pr_artifact(
    existing: Optional[Dict[str, Any]], 
    incoming: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Reducer untuk PRArtifact:
    - Field-level merge untuk data PR.
    - Untuk specifications: memanggil update_specification() untuk menerapkan aturan reset is_confirmed.
    """
    if not existing:
        return incoming or {}
    if not incoming:
        return existing

    merged = {**existing}
    for key, val in incoming.items():
        if key == "specifications" and isinstance(val, list):
            existing_specs = {
                s["field_name"]: (PRSpecification(**s) if isinstance(s, dict) else s) 
                for s in existing.get("specifications", [])
            }
            for new_spec in val:
                fn = new_spec.get("field_name") if isinstance(new_spec, dict) else new_spec.field_name
                new_val = new_spec.get("value") if isinstance(new_spec, dict) else new_spec.value
                new_confirmed = new_spec.get("is_confirmed") if isinstance(new_spec, dict) else new_spec.is_confirmed

                if fn in existing_specs:
                    updated_obj = update_specification(
                        existing=existing_specs[fn],
                        new_value=new_val,
                        new_is_confirmed=new_confirmed if new_confirmed is not None else None
                    )
                    existing_specs[fn] = updated_obj
                else:
                    new_obj = PRSpecification(**new_spec) if isinstance(new_spec, dict) else new_spec
                    existing_specs[fn] = new_obj

            merged["specifications"] = [s.model_dump() for s in existing_specs.values()]
        elif val is not None:
            merged[key] = val

    return merged


def reduce_progress(
    existing: Optional[Dict[str, Any]], 
    incoming: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Reducer untuk RequestProgress: Menggabungkan update status tahapan."""
    if not existing:
        return incoming or {}
    if not incoming:
        return existing
    return {**existing, **{k: v for k, v in incoming.items() if v is not None}}


def reduce_demand(
    existing: Optional[Dict[str, Any]], 
    incoming: Optional[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Reducer untuk DemandBreakdown (Shallow Merge).
    Catatan Arsitektur: Reducer ini murni menggabungkan dict. Proteksi terhadap override manual
    (is_manually_overridden = True) agar tidak ditimpa oleh kalkulasi ulang di-handle secara eksplisit
    di level demand_analysis_node, bukan di reducer ini.
    """
    if incoming is None:
        return existing
    if existing is None:
        return incoming
    return {**existing, **incoming}


def reduce_confirmation_action(
    existing: Optional[bool], 
    incoming: Optional[bool]
) -> bool:
    """Reducer untuk confirmation_action (Single Source of Truth boolean flag untuk aksi konfirmasi spesifikasi)."""
    if incoming is None:
        return bool(existing)
    return bool(incoming)


# ==============================================================================
# 8. Root State Schema (ProcureAIState / GraphState)
# ==============================================================================

class ProcureAIState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    user_context: Dict[str, Any]
    pr: Annotated[Dict[str, Any], reduce_pr_artifact]
    progress: Annotated[Dict[str, Any], reduce_progress]
    demand: Annotated[Optional[Dict[str, Any]], reduce_demand]
    agent_activity: Annotated[List[Dict[str, Any]], reduce_agent_activity]
    attention_items: Annotated[List[Dict[str, Any]], reduce_attention_items]
    recommendation_status: RecommendationStatus
    confirmation_action: Annotated[bool, reduce_confirmation_action]
    next_agent: Literal["Clarification", "Demand", "GeneratePR", "End"]

    # ==========================================================================
    # DEPRECATED: Read-only backward compatibility aliases for legacy test fixtures.
    # Do NOT write to these fields in new nodes or API endpoints.
    # ==========================================================================
    requirement_draft: Optional[Dict[str, Any]]
    demand_analysis: Optional[Dict[str, Any]]
    pr_draft: Optional[Dict[str, Any]]

# GraphState is aliased to ProcureAIState
GraphState = ProcureAIState


def create_initial_graph_state(user_context_dict: Dict[str, Any]) -> ProcureAIState:
    """Helper function to create a blank initial GraphState for a thread."""
    dept = user_context_dict.get("department_id", "DEPT-ENG")
    cc = user_context_dict.get("cost_center", "CC-ENG-001")
    
    initial_progress = RequestProgress(clarification="in_progress")
    initial_pr = PRArtifact(department=dept, cost_center=cc)
    
    return {
        "messages": [],
        "user_context": user_context_dict,
        "pr": initial_pr.model_dump(),
        "progress": initial_progress.model_dump(),
        "demand": None,
        "agent_activity": [],
        "attention_items": [],
        "recommendation_status": "none",
        "confirmation_action": False,
        "next_agent": "Clarification",
        "requirement_draft": RequirementDraftSchema().model_dump(),
        "demand_analysis": DemandAnalysisSchema().model_dump(),
        "pr_draft": None
    }
