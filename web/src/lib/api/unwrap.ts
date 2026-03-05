import type { ApiResponse } from './types';

export function unwrap<T>(res: ApiResponse<T>): T {
  if (!res.success || res.data === null) {
    throw new Error(res.error?.message ?? '알 수 없는 오류가 발생했습니다.');
  }
  return res.data;
}
