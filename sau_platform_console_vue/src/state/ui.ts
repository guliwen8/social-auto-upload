import { reactive } from "vue";

type ToastType = "success" | "error" | "info";

type ConfirmOptions = {
  title: string;
  message?: string;
  confirmText?: string;
  cancelText?: string;
  danger?: boolean;
  inputLabel?: string;
  inputPlaceholder?: string;
  inputRequired?: boolean;
  defaultValue?: string;
};

type ConfirmResult = {
  confirmed: boolean;
  value: string;
};

export const uiState = reactive({
  toastVisible: false,
  toastMessage: "",
  toastType: "info" as ToastType,
  confirmVisible: false,
  confirmTitle: "",
  confirmMessage: "",
  confirmConfirmText: "确认",
  confirmCancelText: "取消",
  confirmDanger: false,
  confirmInputLabel: "",
  confirmInputPlaceholder: "",
  confirmInputRequired: false,
  confirmValue: "",
  _resolve: null as null | ((result: ConfirmResult) => void),
});

let toastTimer: number | undefined;

export function showToast(message: string, type: ToastType = "info") {
  uiState.toastMessage = message;
  uiState.toastType = type;
  uiState.toastVisible = true;
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => {
    uiState.toastVisible = false;
  }, 2400);
}

export function closeToast() {
  uiState.toastVisible = false;
}

export function confirmAction(options: ConfirmOptions): Promise<ConfirmResult> {
  uiState.confirmTitle = options.title;
  uiState.confirmMessage = options.message || "";
  uiState.confirmConfirmText = options.confirmText || "确认";
  uiState.confirmCancelText = options.cancelText || "取消";
  uiState.confirmDanger = Boolean(options.danger);
  uiState.confirmInputLabel = options.inputLabel || "";
  uiState.confirmInputPlaceholder = options.inputPlaceholder || "";
  uiState.confirmInputRequired = Boolean(options.inputRequired);
  uiState.confirmValue = options.defaultValue || "";
  uiState.confirmVisible = true;

  return new Promise((resolve) => {
    uiState._resolve = resolve;
  });
}

export function resolveConfirm(confirmed: boolean) {
  const resolve = uiState._resolve;
  const value = uiState.confirmValue;
  uiState.confirmVisible = false;
  uiState._resolve = null;
  if (resolve) resolve({ confirmed, value });
}

