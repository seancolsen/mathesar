<script lang="ts">
  import { Checkbox } from '@mathesar-components';
  import {
    DEFAULT_COUNT_COL_WIDTH,
    GROUP_MARGIN_LEFT,
  } from '@mathesar/stores/tableData';
  import type {
    TableRecord,
  } from '@mathesar/stores/tableData';

  export let index: number;
  export let isGrouped = false;
  export let primaryKey: string = null;
  export let selected: Record<string | number, boolean>;
  export let row: TableRecord;

  function calculatePKValue(_row, _pkey) {
    if (_pkey && _row?.[_pkey]) {
      return _row[_pkey] as string;
    }
    return null;
  }

  $: primaryKeyValue = calculatePKValue(row, primaryKey);

  function selectionChanged() {
    // Setting selected again to trigger re-render
    selected = { ...selected };
  }
</script>

<div class="cell row-control" style="width:{DEFAULT_COUNT_COL_WIDTH}px;
            left:{isGrouped ? GROUP_MARGIN_LEFT : 0}px">
  <span class="number">{index + 1}</span>

  {#if primaryKeyValue}
    <Checkbox bind:checked={selected[primaryKeyValue]}
      on:change={selectionChanged}/>
  {/if}
</div>
