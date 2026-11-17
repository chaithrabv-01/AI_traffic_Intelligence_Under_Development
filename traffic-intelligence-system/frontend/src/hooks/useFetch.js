import { useCallback, useEffect, useState } from "react";
import { errMsg } from "../services/api.js";

// Runs an async function when the page opens (and when deps change). Returns {data, error, loading, reload}.
export default function useFetch(fetcher, deps = []) {
  const [state, setState] = useState({ data: null, error: null, loading: true });

  const load = useCallback(async () => {
    setState((s) => ({ ...s, loading: true }));
    try {
      setState({ data: await fetcher(), error: null, loading: false });
    } catch (e) {
      setState({ data: null, error: errMsg(e), loading: false });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => { load(); }, [load]);
  return { ...state, reload: load };
}
