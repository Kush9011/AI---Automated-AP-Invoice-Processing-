import streamlit as st
import requests
import pandas as pd
import base64

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="AI AP 3-Way Match System",
    page_icon="📄",
    layout="wide"
)

BACKEND_URL = "http://localhost:8000"

st.title("📄 AI AP 3-Way Match System (Multi-Line)")
st.markdown(
    "Upload Vendor Invoice (Multi-line) → Extract → 3-Way Match → Approve"
)

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "invoice_id" not in st.session_state:
    st.session_state.invoice_id = None

if "invoice_data" not in st.session_state:
    st.session_state.invoice_data = None

if "match_result" not in st.session_state:
    st.session_state.match_result = None

# --------------------------------------------------
# UPLOAD SECTION
# --------------------------------------------------

st.header("1️⃣ Upload Invoice")

uploaded_file = st.file_uploader(
    "Select Invoice PDF (Multi-line supported)",
    type=["pdf"]
)

if uploaded_file is not None:

    col1, col2 = st.columns([2, 1])

    # ----------------------------------------
    # PDF PREVIEW
    # ----------------------------------------

    with col1:

        st.subheader("📄 Invoice Preview")

        pdf_bytes = uploaded_file.getvalue()

        base64_pdf = base64.b64encode(
            pdf_bytes
        ).decode("utf-8")

        pdf_display = f"""
        <iframe
            src="data:application/pdf;base64,{base64_pdf}"
            width="100%"
            height="700"
            type="application/pdf">
        </iframe>
        """

        st.markdown(
            pdf_display,
            unsafe_allow_html=True
        )

    # ----------------------------------------
    # ACTIONS PANEL
    # ----------------------------------------

    with col2:

        st.subheader("Invoice Actions")

        if st.button(
            "📤 Upload & Extract Invoice",
            use_container_width=True
        ):

            try:

                with st.spinner(
                    "Extracting multi-line invoice data..."
                ):

                    response = requests.post(
                        f"{BACKEND_URL}/upload",
                        files={
                            "file": (
                                uploaded_file.name,
                                uploaded_file.getvalue(),
                                "application/pdf"
                            )
                        }
                    )

                if response.status_code == 200:

                    response_data = response.json()
                    invoice_data = response_data.get("data", response_data)

                    st.session_state.invoice_data = invoice_data

                    st.session_state.invoice_id = (
                        invoice_data.get("invoice_id")
                    )

                    line_items_count = response_data.get(
                        "line_items_count",
                        len(invoice_data.get("line_items", []))
                    )

                    st.success(
                        f"✅ Invoice uploaded successfully ({line_items_count} line items)"
                    )

                else:
                    st.error(f"Upload failed: {response.text}")

            except Exception as e:
                st.error(f"Error: {str(e)}")

        # -----------------------------
        # SHOW EXTRACTED DATA
        # -----------------------------

        if st.session_state.invoice_data:

            st.subheader("Extracted Invoice Header")

            # Header info
            header_data = {
                "Invoice ID": st.session_state.invoice_data.get("invoice_id"),
                "PO Number": st.session_state.invoice_data.get("po_number"),
                "Vendor ID": st.session_state.invoice_data.get("vendor_id"),
                "Invoice Date": st.session_state.invoice_data.get("invoice_date"),
            }

            header_df = pd.DataFrame(
                [header_data]
            )

            st.dataframe(
                header_df,
                use_container_width=True,
                hide_index=True
            )

            # Line items table
            st.subheader("Line Items")

            line_items = st.session_state.invoice_data.get("line_items", [])

            if line_items:
                line_items_df = pd.DataFrame(line_items)
                st.dataframe(
                    line_items_df,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.warning("No line items extracted")

# --------------------------------------------------
# RUN MATCH
# --------------------------------------------------

if st.session_state.invoice_id:

    st.header("2️⃣ Run 3-Way Match")

    st.info(
        f"Invoice ID: {st.session_state.invoice_id}"
    )

    if st.button(
        "🔍 Run Line-by-Line Match",
        use_container_width=True
    ):

        try:

            with st.spinner(
                "Running 3-way match on all line items..."
            ):

                response = requests.post(
                    f"{BACKEND_URL}/match/{st.session_state.invoice_id}"
                )

            if response.status_code == 200:

                st.session_state.match_result = (
                    response.json()
                )

                st.success(
                    "✅ Match completed successfully"
                )

            else:
                st.error(f"Match failed: {response.text}")

        except Exception as e:
            st.error(f"Error: {str(e)}")

# --------------------------------------------------
# MATCH RESULTS
# --------------------------------------------------

if st.session_state.match_result:

    result = st.session_state.match_result

    st.header("3️⃣ Match Results")

    status = result.get(
        "status",
        "UNKNOWN"
    )

    # =============================
    # STATUS BANNER & SUMMARY
    # =============================

    summary = result.get("summary", {})

    col1, col2, col3 = st.columns(3)

    with col1:
        if status == "APPROVED":
            st.success(f"✅ {status}")
        elif status == "HOLD":
            st.warning(f"⚠️ {status}")
        else:
            st.error(f"❌ {status}")

    with col2:
        total = summary.get("total_line_items", 0)
        st.metric("Total Line Items", total)

    with col3:
        passed = summary.get("passed_line_items", 0)
        st.metric("Passed Line Items", passed)

    # =============================
    # PO & GR STATUS
    # =============================

    col1, col2 = st.columns(2)

    with col1:
        po_status = result.get("po_status", "UNKNOWN")
        if po_status == "EXISTS":
            st.success(f"✅ PO Exists")
        else:
            st.error(f"❌ PO Missing")

    with col2:
        gr_status = result.get("gr_status", "UNKNOWN")
        if gr_status == "EXISTS":
            st.success(f"✅ GR Exists")
        else:
            st.error(f"❌ GR Missing")

    # =============================
    # LINE ITEM MATCH DETAILS
    # =============================

    if "line_items" in result:

        st.subheader("📊 Line-Item Match Analysis")

        line_items = result.get("line_items", [])

        # Create detailed view for each line item
        for line_item in line_items:
            item_number = line_item.get("item_number")
            item_status = line_item.get("status")
            description = line_item.get("description", "N/A")

            # Color-coded expander
            expander_title = f"Item {item_number}: {description} - {item_status}"

            if item_status == "PASS":
                with st.expander(f"✅ {expander_title}", expanded=False):
                    # Show checks
                    checks = line_item.get("checks", [])
                    checks_df = pd.DataFrame(checks)
                    st.dataframe(
                        checks_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "check_name": st.column_config.TextColumn("Check"),
                            "invoice_value": st.column_config.TextColumn("Invoice"),
                            "po_value": st.column_config.TextColumn("PO"),
                            "gr_value": st.column_config.TextColumn("GR"),
                            "result": st.column_config.TextColumn("Result")
                        }
                    )
            else:
                with st.expander(f"❌ {expander_title}", expanded=True):
                    # Show checks with highlighting
                    checks = line_item.get("checks", [])
                    checks_df = pd.DataFrame(checks)
                    st.dataframe(
                        checks_df,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "check_name": st.column_config.TextColumn("Check"),
                            "invoice_value": st.column_config.TextColumn("Invoice"),
                            "po_value": st.column_config.TextColumn("PO"),
                            "gr_value": st.column_config.TextColumn("GR"),
                            "result": st.column_config.TextColumn("Result")
                        }
                    )

                    if item_status == "FAIL":
                        st.error(
                            f"⚠️ This line item has discrepancies. Review the checks above."
                        )

    # =============================
    # ERROR MESSAGE
    # =============================

    if "error" in result:
        st.error(f"Error: {result.get('error')}")

    # =============================
    # APPROVE INVOICE
    # =============================

    if status == "APPROVED":

        st.header("4️⃣ Approval")

        if st.button(
            "✅ Approve & Move to Final",
            use_container_width=True
        ):

            try:

                response = requests.post(
                    f"{BACKEND_URL}/approve/{st.session_state.invoice_id}"
                )

                if response.status_code == 200:

                    st.success(
                        "✅ Invoice moved to final table and approved!"
                    )

                    approval_data = response.json()
                    st.json(approval_data)

                else:
                    st.error(
                        response.text
                    )

            except Exception as e:
                st.error(str(e))

    # =============================
    # RAW RESPONSE
    # =============================

    with st.expander(
        "🔧 View Raw Match Response"
    ):

        st.json(result)
