"""
Google Forms API wrapper.
"""

from typing import List, Optional

from googleapiclient.errors import HttpError

from app.auth.clients import build_forms_service
from app.core.exceptions import GoogleWorkspaceError, normalize_google_error
from app.services.drive_service import DriveService

QUESTION_TYPES = {
    "short_answer": "TEXT",
    "paragraph": "PARAGRAPH_TEXT",
    "multiple_choice": "RADIO",
    "checkbox": "CHECKBOX",
}


class FormsService:
    def __init__(
        self,
        credentials_path: Optional[str] = None,
        credentials_json: Optional[str] = None,
    ):
        self._forms = build_forms_service(
            credentials_path=credentials_path,
            credentials_json=credentials_json,
        )
        self._drive = DriveService(
            credentials_path=credentials_path,
            credentials_json=credentials_json,
        )

    def create_form(
        self,
        title: str = "Untitled form",
        parent_folder_id: Optional[str] = None,
    ) -> dict:
        try:
            form = self._forms.forms().create(body={"info": {"title": title}}).execute()
        except HttpError as e:
            raise normalize_google_error(e)
        form_id = form["formId"]
        parent_applied, parent_error = self._drive.apply_parent(
            form_id, parent_folder_id
        )
        return {
            "form_id": form_id,
            "title": form.get("info", {}).get("title", title),
            "responder_uri": form.get("responderUri"),
            "parent_applied": parent_applied,
            "parent_error": parent_error,
        }

    def get_form(self, form_id: str) -> dict:
        try:
            form = self._forms.forms().get(formId=form_id).execute()
            questions = []
            for item in form.get("items", []):
                question = item.get("questionItem", {}).get("question", {})
                qtype = None
                if "textQuestion" in question:
                    qtype = (
                        "paragraph"
                        if question["textQuestion"].get("paragraph")
                        else "short_answer"
                    )
                elif "choiceQuestion" in question:
                    ctype = question["choiceQuestion"].get("type")
                    qtype = "checkbox" if ctype == "CHECKBOX" else "multiple_choice"
                questions.append(
                    {
                        "item_id": item.get("itemId"),
                        "question_id": question.get("questionId"),
                        "title": item.get("title"),
                        "question_type": qtype,
                    }
                )
            info = form.get("info", {})
            return {
                "form_id": form_id,
                "title": info.get("title"),
                "description": info.get("description"),
                "responder_uri": form.get("responderUri"),
                "questions": questions,
            }
        except HttpError as e:
            raise normalize_google_error(e)

    def update_info(
        self,
        form_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> None:
        if title is None and description is None:
            raise GoogleWorkspaceError(
                "Provide title and/or description",
                error_code="VALIDATION_ERROR",
                retryable=False,
            )
        try:
            update = {"info": {}}
            mask_fields = []
            if title is not None:
                update["info"]["title"] = title
                mask_fields.append("title")
            if description is not None:
                update["info"]["description"] = description
                mask_fields.append("description")
            self._forms.forms().batchUpdate(
                formId=form_id,
                body={
                    "requests": [
                        {
                            "updateFormInfo": {
                                "info": update["info"],
                                "updateMask": ",".join(mask_fields),
                            }
                        }
                    ]
                },
            ).execute()
        except HttpError as e:
            raise normalize_google_error(e)

    def add_question(
        self,
        form_id: str,
        title: str,
        question_type: str = "short_answer",
        options: Optional[List[str]] = None,
        required: bool = False,
        index: int = 0,
    ) -> dict:
        if question_type not in QUESTION_TYPES:
            raise GoogleWorkspaceError(
                f"Unsupported question_type: {question_type}. "
                f"Supported: {', '.join(sorted(QUESTION_TYPES))}",
                error_code="VALIDATION_ERROR",
                retryable=False,
            )
        if question_type in ("multiple_choice", "checkbox") and not options:
            raise GoogleWorkspaceError(
                "options required for multiple_choice and checkbox",
                error_code="VALIDATION_ERROR",
                retryable=False,
            )
        try:
            question: dict = {"required": required}
            api_type = QUESTION_TYPES[question_type]
            if api_type in ("TEXT", "PARAGRAPH_TEXT"):
                question["textQuestion"] = {"paragraph": api_type == "PARAGRAPH_TEXT"}
            else:
                question["choiceQuestion"] = {
                    "type": api_type,
                    "options": [{"value": opt} for opt in (options or [])],
                }

            result = (
                self._forms.forms()
                .batchUpdate(
                    formId=form_id,
                    body={
                        "requests": [
                            {
                                "createItem": {
                                    "item": {
                                        "title": title,
                                        "questionItem": {"question": question},
                                    },
                                    "location": {"index": index},
                                }
                            }
                        ]
                    },
                )
                .execute()
            )
            created = result.get("replies", [{}])[0].get("createItem", {})
            item_id = created.get("itemId")
            question_ids = created.get("questionId", [])
            return {
                "item_id": item_id,
                "question_id": question_ids[0] if question_ids else None,
            }
        except HttpError as e:
            raise normalize_google_error(e)

    def list_responses(
        self,
        form_id: str,
        page_size: int = 50,
        page_token: Optional[str] = None,
        include_answers: bool = False,
    ) -> dict:
        try:
            kwargs = {"formId": form_id, "pageSize": min(max(page_size, 1), 5000)}
            if page_token:
                kwargs["pageToken"] = page_token
            result = self._forms.forms().responses().list(**kwargs).execute()
            responses = []
            for resp in result.get("responses", []):
                entry = {
                    "response_id": resp.get("responseId"),
                    "create_time": resp.get("createTime"),
                    "last_submitted_time": resp.get("lastSubmittedTime"),
                }
                if include_answers:
                    entry["answers"] = self._simplify_answers(resp.get("answers", {}))
                responses.append(entry)
            return {
                "responses": responses,
                "next_page_token": result.get("nextPageToken"),
            }
        except HttpError as e:
            raise normalize_google_error(e)

    def get_response(
        self,
        form_id: str,
        response_id: str,
        include_answers: bool = False,
    ) -> dict:
        try:
            resp = (
                self._forms.forms()
                .responses()
                .get(formId=form_id, responseId=response_id)
                .execute()
            )
            result = {
                "response_id": resp.get("responseId"),
                "create_time": resp.get("createTime"),
                "last_submitted_time": resp.get("lastSubmittedTime"),
            }
            if include_answers:
                result["answers"] = self._simplify_answers(resp.get("answers", {}))
            return result
        except HttpError as e:
            raise normalize_google_error(e)

    @staticmethod
    def _simplify_answers(answers: dict) -> dict:
        simplified = {}
        for qid, answer in (answers or {}).items():
            text_answers = answer.get("textAnswers", {}).get("answers", [])
            if text_answers:
                simplified[qid] = [a.get("value") for a in text_answers]
            else:
                simplified[qid] = answer
        return simplified
