import sys
import unittest
import warnings

import numpy as np
import pandas as pd
from mock import MagicMock, PropertyMock, patch

from trane.core.prediction_problem import PredictionProblem
from trane.ops.aggregation_ops import LastAggregationOp
from trane.ops.filter_ops import AllFilterOp
from trane.ops.row_ops import IdentityRowOp
from trane.ops.transformation_ops import IdentityTransformationOp
from trane.utils.table_meta import TableMeta

dataframe = pd.DataFrame(
    [(0, 0, 0, 5.32, 19.7, 53.89, 1),
     (0, 0, 1, 1.08, 6.78, 18.89, 2),
     (0, 0, 2, 4.69, 14.11, 41.35, 4)],
    columns=["vendor_id", "taxi_id", "trip_id", "distance",
             "duration", "fare", "num_passengers"])

json_str = '{ "path": "", "tables": [ { "path": "synthetic_taxi_data.csv", \
    "name": "taxi_data", "fields": [ {"name": "vendor_id", "type": "id"},\
    {"name": "taxi_id", "type": "id"}, \
    {"name": "trip_id", "type": "datetime"},\
    {"name": "distance", "type": "number", "subtype": "float"},\
    {"name": "duration", "type": "number", "subtype": "float"},\
    {"name": "fare", "type": "number", "subtype": "float"},\
    {"name": "num_passengers", "type": "number", "subtype": "float"} ] } ]}'

dataframe2 = pd.DataFrame([(0, 0),
                           (1, 1),
                           (2, 2),
                           (3, 3),
                           (4, 4),
                           (5, 5),
                           (6, 6),
                           (7, 7),
                           (8, 8),
                           (9, 9)], columns=['c1', 'c2'])


def test_to_and_from_json_with_order_of_types():
    label_generating_column = "fare"
    operations = [AllFilterOp(label_generating_column),
                  IdentityRowOp(label_generating_column),
                  IdentityTransformationOp(label_generating_column),
                  LastAggregationOp(label_generating_column)]
    prediction_problem = PredictionProblem(
        operations=operations, cutoff_strategy=None)
    prediction_problem.filter_column_order_of_types = [TableMeta.TYPE_INTEGER]
    prediction_problem.label_generating_column_order_of_types = \
        [TableMeta.TYPE_INTEGER, TableMeta.TYPE_BOOL, TableMeta.TYPE_CATEGORY]
    json_str = prediction_problem.to_json()
    prediction_problem_from_json = PredictionProblem.from_json(json_str)

    assert(prediction_problem == prediction_problem_from_json)


class TestPredictionProblemMethods(unittest.TestCase):

    def setUp(self):
        mock_op = self.create_patch(
            'trane.ops.OpBase')
        self.operations = [mock_op for x in range(4)]

        self.mock_cutoff_strategy = self.create_patch(
            'trane.core.CutoffStrategy')

        self.entity_col = 'entity_col'
        self.time_col = 'time_col'

        self.problem = PredictionProblem(
            operations=self.operations, entity_id_col=self.entity_col,
            time_col=self.time_col, cutoff_strategy=self.mock_cutoff_strategy)

        self.mock_dill = self.create_patch(
            'trane.core.prediction_problem.dill')

    def create_patch(self, name):
        # helper method for creating patches
        patcher = patch(name)
        thing = patcher.start()
        self.addCleanup(patcher.stop)
        return thing

    def test_attributes_assigned(self):
        self.assertEqual(self.problem.operations, self.operations)
        self.assertEqual(self.problem.entity_id_col, self.entity_col)
        self.assertEqual(self.problem.time_col, self.time_col)
        self.assertEqual(self.problem.cutoff_strategy,
                         self.mock_cutoff_strategy)

    def test_equality_false(self):
        entity_id = 'entity_col'
        mock_op = MagicMock()
        operations = [mock_op for x in range(4)]
        mock_cutoff_strategy = MagicMock()
        problem_1 = PredictionProblem(
            operations=operations, entity_id_col=entity_id,
            cutoff_strategy=mock_cutoff_strategy)

        # add a different magicmock for cutoff strategy
        problem_2 = PredictionProblem(
            operations=operations, entity_id_col=entity_id,
            cutoff_strategy=MagicMock())
        self.assertFalse(problem_1 == problem_2)

    def test_equality_false_diff_types(self):
        other_obj = 'a string'
        self.assertFalse(self.problem == other_obj)

    def test_equality_true(self):
        entity_id = 'entity_col'
        mock_op = MagicMock()
        operations = [mock_op for x in range(4)]
        mock_cutoff_strategy = MagicMock()
        problem_1 = PredictionProblem(
            operations=operations, entity_id_col=entity_id,
            cutoff_strategy=mock_cutoff_strategy)

        problem_2 = PredictionProblem(
            operations=operations, entity_id_col=entity_id,
            cutoff_strategy=mock_cutoff_strategy)
        self.assertTrue(problem_1 == problem_2)

    def test_cutoff_strategy_exists(self):
        self.assertIsNotNone(self.problem.cutoff_strategy)

    def entity_id_col_exists(self):
        self.assertIsNot(self.problem.entity_id_col)

    def test_to_json_exists(self):
        self.assertIsNotNone(self.problem.to_json)

    def test_save(self):
        self.assertIsNotNone(self.problem.save)

        dill_cutoff_strategy_patch = self.create_patch(
            'trane.core.PredictionProblem._dill_cutoff_strategy')
        os_path_exists_patch = self.create_patch(
            'trane.core.prediction_problem.os.path.exists')
        os_path_exists_patch.return_value = False
        to_json_patch = self.create_patch(
            'trane.core.PredictionProblem.to_json')
        dill_cutoff_strategy_patch = self.create_patch(
            'trane.core.PredictionProblem._dill_cutoff_strategy')
        json_patch = self.create_patch(
            'trane.core.prediction_problem.json')

        path_patch = self.create_patch(
            'trane.core.prediction_problem.os.path.isdir')
        path_patch.return_value = False
        makedirs_patch = self.create_patch(
            'trane.core.prediction_problem.os.makedirs')

        path = '../Data'
        problem_name = 'problem_name'

        open_patch = None
        if (sys.version_info > (3, 0)):
            open_patch = self.create_patch('builtins.open')
        else:
            open_patch = self.create_patch('__builtin__.open')

        # Save
        self.problem.save(path=path, problem_name=problem_name)

        self.assertTrue(dill_cutoff_strategy_patch.called)
        self.assertTrue(os_path_exists_patch.called)
        self.assertTrue(to_json_patch.called)
        self.assertTrue(path_patch.called)
        self.assertTrue(makedirs_patch.called)
        self.assertTrue(json_patch.loads.called)
        self.assertTrue(open_patch.called)

    def test_load(self):
        self.assertIsNotNone(PredictionProblem.load)

        open_patch = None
        if (sys.version_info > (3, 0)):
            open_patch = self.create_patch('builtins.open')
        else:
            open_patch = self.create_patch('__builtin__.open')

        json_patch = self.create_patch(
            'trane.core.prediction_problem.json')
        from_json_patch = self.create_patch(
            'trane.core.PredictionProblem.from_json')
        os_path_patch = self.create_patch(
            'trane.core.prediction_problem.os.path')
        dill_patch = self.create_patch(
            'trane.core.prediction_problem.dill')

        PredictionProblem.load('filepath.json')
        self.assertTrue(open_patch.called)
        self.assertTrue(json_patch.load.called)
        self.assertTrue(from_json_patch.called)
        self.assertTrue(os_path_patch.join.called)
        self.assertTrue(os_path_patch.dirname.called)
        self.assertTrue(dill_patch.load.called)

    def test_dill_cutoff_strategy(self):
        self.assertIsNotNone(self.problem._dill_cutoff_strategy)
        cutoff_dill = self.problem._dill_cutoff_strategy()

        self.assertEqual(
            cutoff_dill, self.mock_dill.dumps(self.mock_cutoff_strategy))

    def test_is_valid_succeeds(self):
        self.assertIsNotNone(self.problem.is_valid)

        table_meta_mock = MagicMock()
        table_meta_mock.copy.return_value = table_meta_mock

        for op in self.problem.operations:
            op.op_type_check.return_value = table_meta_mock

        self.assertTrue(
            self.problem.is_valid(table_meta=table_meta_mock))

        self.assertTrue(table_meta_mock.copy.called)
        for op in self.problem.operations:
            self.assertTrue(op.op_type_check.called)
            self.assertTrue(op.op_type_check.call_args[
                            0][0] == table_meta_mock)

    def test_is_valid_fails(self):
        table_meta_mock = MagicMock()
        table_meta_mock.copy.return_value = table_meta_mock

        for op in self.problem.operations:
            op.op_type_check.return_value = None

        self.assertFalse(
            self.problem.is_valid(table_meta=table_meta_mock))

        self.assertTrue(table_meta_mock.copy.called)

    def test_is_valid_substitutes_object_val(self):
        table_meta_mock = MagicMock(name='table_meta_mock')
        table_meta_mock.copy.return_value = table_meta_mock

        for op in self.problem.operations:
            op.op_type_check.return_value = table_meta_mock

        # fails without provided table_meta
        self.problem.table_meta = None
        with self.assertRaises(Exception):
            self.problem.is_valid()

        # uses local table_meta if assigned
        table_meta_mock = MagicMock(name='table_meta_mock')
        self.problem.table_meta = table_meta_mock
        self.problem.is_valid()
        # self.assertTrue(table_meta_mock.called)

    def test_execute_operations_on_df(self):
        mock_df = MagicMock()
        mock_df.copy.return_value = mock_df
        self.operations[0].execute.return_value = mock_df

        self.problem._execute_operations_on_df(mock_df)

        # the operation has been called as many times as there are operations
        # remember, all operations are actually the same mock in set_up
        self.assertEqual(
            self.operations[0].execute.call_count, len(self.operations))

        # the operation is passed the mock_df
        self.assertEqual(
            self.operations[0].execute.call_args[0][0], mock_df)

    def test_rename_columns(self):
        self.assertIsNotNone(self.problem._rename_columns)

        mock_df = MagicMock()
        column_list = ('a', 'b', 'c')

        names = PropertyMock(return_value=['D'])
        type(mock_df.index).names = names

        values = PropertyMock(return_value=[0, 1])
        type(mock_df.columns).values = values

        self.problem._rename_columns(mock_df, column_list)

        self.assertEqual(mock_df.index.names, ['D'])
        self.assertTrue(mock_df.rename.called)

    def test_execute_raises_if_not_valid(self):
        is_valid_mock = MagicMock()
        self.problem.is_valid = is_valid_mock
        is_valid_mock.return_value = False

        with self.assertRaises(ValueError):
            self.problem.execute('foo')

    def test_execute(self):
        '''
        This method is central to Trane running, so is getting an integration
        test.
        '''
        self.assertIsNotNone(self.problem.execute)
        df = pd.DataFrame(
            [(100, 0, 0, 5.32, 19.7, 53.89, 1, np.datetime64('2000-01-01')),
             (200, 0, 1, 1.08, 6.78, 18.89, 2, np.datetime64('2000-01-01')),
             (100, 0, 2, 4.69, 14.11, 41.35, 4, np.datetime64('2000-01-01'))],
            columns=[
                "vendor_id", "taxi_id", "trip_id", "distance",
                "duration", "fare", "num_passengers", "date"])

    #     # set some things on this problem, since it's an integration test
        static_cutoff = np.datetime64('1980-02-25')
        self.mock_cutoff_strategy.generate_fn.return_value = static_cutoff
        self.entity_col = 'vendor_id'
        self.time_col = 'date'

        # operation.execute all return the same thing
        op_mock = MagicMock(name='operation')
        op_mock.execute.return_value = pd.DataFrame(
            [[1, 2, 0]], columns=[self.entity_col, 'a', 'fare'])
        operations = [op_mock for x in range(4)]

        # prediction problem gets new mock operations
        self.problem = PredictionProblem(
            operations=operations, entity_id_col=self.entity_col,
            time_col=self.time_col, label_col='fare',
            cutoff_strategy=self.mock_cutoff_strategy)

        is_valid_mock = MagicMock()
        self.problem.is_valid = is_valid_mock
        is_valid_mock.return_value = True

        # _execute_operations_on_df and _insert_single_row_into_dict
        # are actually tested as part of integration

        res = self.problem.execute(df)
        self.assertEqual(res.columns.tolist(), ['cutoff', 'label'])
        self.assertEqual(set(res.index.tolist()), set([100, 200]))
        self.assertEqual(res.loc[100]['label'], 0)
        self.assertEqual(res.loc[200]['label'], 0)

    def test_insert_single_label_into_dict_happy_path(self):
        self.assertIsNotNone(self.problem._insert_single_label_into_dict)

        entity_id = 'entity_id'
        cutoff = 'cutoff'

        res_dict = {}
        label_series = pd.Series([1])
        entity_id = '12345'

        # assert no warnings RuntimeWarningsed
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            res_dict = self.problem._insert_single_label_into_dict(
                entity_id, label_series, cutoff, res_dict)
            assert len(w) == 0

        self.assertEqual(res_dict[entity_id][0], cutoff)
        self.assertEqual(res_dict[entity_id][1], 1)

    def test_insert_single_label_into_dict_warn_gt1_path(self):

        entity_id = 'entity_id'
        cutoff = 'cutoff'

        res_dict = {}
        label_series = pd.Series([1, 2])
        entity_id = '12345'

        # assert no warnings RuntimeWarningsed
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            res_dict = self.problem._insert_single_label_into_dict(
                entity_id, label_series, cutoff, res_dict)
            assert len(w) == 1

        self.assertEqual(res_dict[entity_id][0], cutoff)
        # assert that the method still picks the first row in the df
        self.assertEqual(res_dict[entity_id][1], 1)

    def test_insert_single_label_into_dict_warn_lt1_path(self):

        entity_id = 'entity_id'
        cutoff = 'cutoff'

        res_dict = {}
        label_df = pd.Series()
        entity_id = '12345'

        # assert no warnings RuntimeWarningsed
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            res_dict = self.problem._insert_single_label_into_dict(
                entity_id, label_df, cutoff, res_dict)
            assert len(w) == 1

        # assert that the results dict is untouched
        self.assertEqual(res_dict, {})

    def test_str(self):
        self.assertIsNotNone(self.problem.__str__)

        # mock some operations
        mock_op = MagicMock()
        mock_op.__str__.return_value = 'foo'
        operations = [mock_op for x in range(4)]
        self.problem.operations = operations

        description = self.problem.__str__()
        self.assertEqual(description, 'foo->foo->foo->foo')
