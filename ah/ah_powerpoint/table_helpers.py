from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls
from pptx.table import _Cell, _Row, _Column
from random import randrange
import copy

def add_column(table):
    """
    Duplicates the last column of the table and appends it to the end.
    """
    new_col = copy.deepcopy(table._tbl.tblGrid.gridCol_lst[-1])
    table._tbl.tblGrid.append(new_col)  # copies last grid element

    for tr in table._tbl.tr_lst:
        # duplicate last cell of each row
        new_tc = copy.deepcopy(tr.tc_lst[-1])

        # Fix for column styling
        last_tc = tr.xpath(".//a:tc")[-1]
        parent = last_tc.getparent()
        parent.insert(
            parent.index(last_tc) + 1,
            new_tc
        )

        # Clear new cell content
        cell = _Cell(new_tc, tr.tc_lst)
        cell.text_frame.clear()

    # Fix column not writable
    # https://stackoverflow.com/questions/64591452/using-copy-deepcopy-with-python-pptx-to-add-a-column-to-a-table-leads-to-cell-at
    from pptx import oxml
    for child in table._tbl.getchildren():
        if isinstance(child, oxml.table.CT_TableGrid):
            ws = set()
            for j in child:
                if j.w not in ws:
                    ws.add(j.w)
                else:
                    for elem in j:
                        j.remove(elem)

    # Create object in memory, in case some operations are done by the library
    col = _Column(new_col, table)

def remove_column(table, column_index: int):
    """
    Removes a specified column from the table.
    """
    column = list(table.columns)[column_index]

    col_idx = table._tbl.tblGrid.index(column._gridCol)

    for tr in table._tbl.tr_lst:
        tr.remove(tr.tc_lst[col_idx])

    table._tbl.tblGrid.remove(column._gridCol)

def add_row(table) -> None:
    """Adds a new row to the table, creating a default row if the table is empty."""
    ns = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
    if len(table._tbl.tr_lst) == 0:
        # Table is empty, create a new row from scratch
        new_row = parse_xml(f'<a:tr xmlns:a="{ns["a"]}"><a:tc><a:txBody><a:bodyPr/><a:lstStyle/><a:p/></a:txBody></a:tc></a:tr>')
        # Add cells to match the number of columns
        for _ in range(len(table.columns) - 1):  # -1 because we already added one cell
            new_cell = parse_xml(f'<a:tc xmlns:a="{ns["a"]}"><a:txBody><a:bodyPr/><a:lstStyle/><a:p/></a:txBody></a:tc>')
            new_row.append(new_cell)
    else:
        # Copy the last row
        new_row = table._tbl.tr_lst[-1].deepcopy()

    for tc in new_row.tc_lst:
        cell = _Cell(tc, new_row.tc_lst)
        cell.text = ''

    table._tbl.append(new_row)
    row = _Row(new_row, table)

    # Fix row not writable
    reference = row._tr.xpath(".//a:ext", namespaces=ns)[0]
    reference.getchildren()[0].set("val", str(randrange(10 ** 5, 10 ** 9)))

def remove_row(table, row_index: int) -> None:
    """
    Remove a specified row from the table.

    :return:
    """
    row = list(table.rows)[row_index]

    table._tbl.remove(row._tr)
