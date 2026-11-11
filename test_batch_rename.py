import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from batch_rename import BatchRenameApp


class RenameTests(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory(
            prefix="rename_test_", dir=Path(__file__).resolve().parent
        )
        self.addCleanup(folder.cleanup)
        self.folder = Path(folder.name)
        self.app = BatchRenameApp.__new__(BatchRenameApp)
        self.app.current_dir = str(self.folder)
        self.app.selection_mode = "directory"
        self.app.files = []
        self.app.rename_history = []
        for feature in (
            "reverse", "delete_text", "replace", "prefix", "suffix",
            "sequence", "regex", "case", "ext",
        ):
            setattr(self.app, "enable_" + feature, Mock(get=Mock(return_value=False)))
        self.app.enable_ext.get.return_value = True
        self.app.entry_new_ext = Mock(get=Mock(return_value=".JPG"))
        for entry, value in {
            "delete_text": "", "find": "", "replace": "", "prefix": "",
            "suffix": "", "base_name": "", "start_num": "1", "digits": "3",
            "regex": "", "regex_replace": "",
        }.items():
            setattr(self.app, "entry_" + entry, Mock(get=Mock(return_value=value)))
        self.app.replace_all_var = Mock(get=Mock(return_value=True))
        self.app.case_mode = Mock(get=Mock(return_value="lower"))
        self.app.filter_ext = Mock(get=Mock(return_value=""))
        self.app.filter_keyword = Mock(get=Mock(return_value=""))
        self.app.status_var = Mock()
        self.app.file_count_var = Mock()
        self.app.path_var = Mock()
        self.app._update_file_tree = Mock()
        messages = patch("batch_rename.messagebox")
        self.messages = messages.start()
        self.addCleanup(messages.stop)
        self.messages.askyesno.return_value = True

    def add_file(self, name, content=b"original image content"):
        path = self.folder / name
        path.write_bytes(content)
        return path

    def configure(self, *features, **values):
        for feature in (
            "reverse", "delete_text", "replace", "prefix", "suffix",
            "sequence", "regex", "case", "ext",
        ):
            getattr(self.app, "enable_" + feature).get.return_value = feature in features
        for name, value in values.items():
            getattr(self.app, name).get.return_value = value

    def snapshot(self):
        return {p.name: p.read_bytes() for p in self.folder.iterdir() if p.is_file()}

    def test_each_name_transformation(self):
        cases = [
            ("delete_text", {"entry_delete_text": "old_"}, "old_photo.jpg", "photo.jpg"),
            ("delete_text", {"entry_delete_text": " "}, "my photo.jpg", "myphoto.jpg"),
            ("replace", {"entry_find": "a", "entry_replace": "b"}, "aaa.jpg", "bbb.jpg"),
            ("replace", {"entry_find": "a", "entry_replace": "b", "replace_all_var": False}, "aaa.jpg", "baa.jpg"),
            ("prefix", {"entry_prefix": "新_"}, "photo.jpg", "新_photo.jpg"),
            ("suffix", {"entry_suffix": "_副本"}, "photo.jpg", "photo_副本.jpg"),
            ("case", {"case_mode": "lower"}, "My PHOTO.JPG", "my photo.JPG"),
            ("case", {"case_mode": "upper"}, "My photo.jpg", "MY PHOTO.jpg"),
            ("case", {"case_mode": "title"}, "my photo.jpg", "My Photo.jpg"),
            ("case", {"case_mode": "camel"}, "my-photo_test.jpg", "myPhotoTest.jpg"),
            ("case", {"case_mode": "camel"}, "_my-photo.jpg", "myPhoto.jpg"),
            ("regex", {"entry_regex": r"(photo)_(\d+)", "entry_regex_replace": r"\2-\1"}, "photo_12.jpg", "12-photo.jpg"),
            ("ext", {"entry_new_ext": "PNG"}, "photo.jpg", "photo.PNG"),
            ("sequence", {"entry_start_num": "0", "entry_digits": "2"}, "photo.jpg", "00.jpg"),
        ]
        for feature, values, original, expected in cases:
            with self.subTest(feature=feature, original=original):
                self.configure(feature, **values)
                self.app.files = [{"name": original}]
                self.assertEqual(self.app._generate_new_names(), [expected])

    def test_reverse_preview_matches_execution(self):
        self.add_file("a.txt", b"A")
        self.add_file("b.txt", b"B")
        self.app._load_files()
        self.configure("reverse", "sequence", entry_base_name="item", entry_digits="1")
        del self.app._update_file_tree
        self.app.file_tree = Mock()
        self.app.file_tree.get_children.return_value = []
        self.app.colors = {"preview_new": "green"}

        self.app._preview_rename()
        rows = [call.kwargs["values"] for call in self.app.file_tree.insert.call_args_list]
        self.assertEqual([(row[1], row[2]) for row in rows], [("b.txt", "item1.txt"), ("a.txt", "item2.txt")])

        self.app._execute_rename()
        self.assertEqual(self.snapshot(), {"item1.txt": b"B", "item2.txt": b"A"})

    def test_numbering_can_move_into_names_from_same_batch(self):
        self.add_file("1.txt", b"one")
        self.add_file("2.txt", b"two")
        self.app._load_files()
        self.configure("sequence", entry_start_num="2", entry_digits="1")

        self.app._execute_rename()
        self.assertEqual(self.snapshot(), {"2.txt": b"one", "3.txt": b"two"})
        self.app._undo_last_rename()
        self.assertEqual(self.snapshot(), {"1.txt": b"one", "2.txt": b"two"})

    def test_reverse_numbering_can_swap_names(self):
        originals = {"1.txt": b"one", "2.txt": b"two", "3.txt": b"three"}
        for name, content in originals.items():
            self.add_file(name, content)
        self.app._load_files()
        self.configure("reverse", "sequence", entry_digits="1")

        self.app._execute_rename()
        self.assertEqual(self.snapshot(), {"1.txt": b"three", "2.txt": b"two", "3.txt": b"one"})
        self.app._undo_last_rename()
        self.assertEqual(self.snapshot(), originals)

    def test_duplicate_targets_are_rejected_before_any_changes(self):
        self.add_file("a.txt", b"A")
        self.add_file("b.txt", b"B")
        self.app._load_files()
        self.configure("regex", entry_regex="^[ab]$", entry_regex_replace="same")
        before = self.snapshot()

        self.app._execute_rename()
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.app.rename_history, [])
        self.messages.showerror.assert_called_once()

    def test_invalid_windows_names_are_rejected_in_preview(self):
        for name in ("../escape", "sub\\file", "CON", "nul.txt", "a:b", "a?b", "a*", "a|b", "a<", 'a"', "a>", "a\x00", "a.", "a ", "", "x" * 256):
            with self.subTest(name=name):
                self.app.files = [{"name": "source"}]
                self.configure("replace", entry_find="source", entry_replace=name)
                self.assertIsNone(self.app._generate_new_names())

    def test_bad_regex_replacement_is_reported_without_crashing(self):
        self.app.files = [{"name": "source.txt"}]
        self.configure("regex", entry_regex="(source)", entry_regex_replace=r"\g<missing>")
        self.assertIsNone(self.app._generate_new_names())
        self.messages.showerror.assert_called_once()

    def test_extension_filter_ignores_empty_tokens(self):
        self.app.files = [{"name": "a.JPG"}, {"name": "b.png"}, {"name": "c.notjpg"}]
        for value in (".jpg,", "jpg", " .JPG， "):
            with self.subTest(filter=value):
                self.app.filter_ext.get.return_value = value
                self.assertEqual(self.app._apply_filter(self.app.files), [{"name": "a.JPG"}])

    def test_invalid_sequence_settings_are_rejected(self):
        self.app.files = [{"name": "source.txt"}]
        for start, digits in (("-1", "3"), ("1", "-1"), ("1", "0"), ("1", "256"), ("x", "3")):
            with self.subTest(start=start, digits=digits):
                self.configure("sequence", entry_start_num=start, entry_digits=digits)
                self.assertIsNone(self.app._generate_new_names())

    def test_failed_undo_can_be_retried(self):
        source = self.add_file("photo.png", b"original")
        self.app._load_files()
        self.app._execute_rename()
        source.write_bytes(b"other")
        self.app._undo_last_rename()
        self.assertEqual(len(self.app.rename_history), 1)

        source.unlink()
        self.app._undo_last_rename()
        self.assertEqual(self.snapshot(), {"photo.png": b"original"})
        self.assertEqual(self.app.rename_history, [])

    def test_empty_file_selection_does_not_reload_previous_folder(self):
        self.add_file("unselected.txt")
        self.app.selection_mode = "files"
        self.app.files = []
        self.app._refresh_files()
        self.assertEqual(self.app.files, [])

    def test_transformations_execute_and_undo_with_contents_preserved(self):
        cases = [
            ("delete_text", {"entry_delete_text": " "}, "my photo.JPG", "myphoto.JPG"),
            ("replace", {"entry_find": "旧", "entry_replace": "新"}, "旧旧.txt", "新新.txt"),
            ("replace", {"entry_find": "旧", "entry_replace": "新", "replace_all_var": False}, "旧旧.txt", "新旧.txt"),
            ("prefix", {"entry_prefix": "备份_"}, "文件.txt", "备份_文件.txt"),
            ("suffix", {"entry_suffix": "_完成"}, "photo.tar.gz", "photo.tar_完成.gz"),
            ("case", {"case_mode": "lower"}, "PHOTO.JPG", "photo.JPG"),
            ("case", {"case_mode": "upper"}, "photo.jpg", "PHOTO.jpg"),
            ("case", {"case_mode": "title"}, "my photo.txt", "My Photo.txt"),
            ("case", {"case_mode": "camel"}, "_my--photo_test.txt", "myPhotoTest.txt"),
            ("regex", {"entry_regex": r"(图)_(\d+)", "entry_regex_replace": r"\2-\1"}, "图_12.jpg", "12-图.jpg"),
            ("sequence", {"entry_base_name": "图片", "entry_start_num": "9", "entry_digits": "3"}, "original", "图片009"),
            ("prefix", {"entry_prefix": "备份_"}, ".hidden", "备份_.hidden"),
            ("ext", {"entry_new_ext": "png"}, "照片😀.jpg", "照片😀.png"),
        ]
        for i, (feature, settings, source, target) in enumerate(cases):
            with self.subTest(feature=feature, source=source):
                content = ("original-" + str(i)).encode()
                original = self.add_file(source, content)
                self.app._load_files()
                self.configure(feature, **settings)
                self.app._execute_rename()
                self.assertEqual(self.snapshot(), {target: content})
                self.app._undo_last_rename()
                self.assertEqual(self.snapshot(), {source: content})
                self.assertEqual(self.app.rename_history, [])
                original.unlink()

    def test_text_options_combine_in_documented_order(self):
        self.add_file("old_photo__2024.jpg", b"image")
        self.app._load_files()
        self.configure(
            "delete_text", "replace", "prefix", "suffix", "regex", "case", "ext",
            entry_delete_text="old_", entry_find="photo", entry_replace="image",
            entry_prefix="new_", entry_suffix="_done", entry_regex="_+", entry_regex_replace="-",
            case_mode="upper", entry_new_ext="PNG",
        )
        self.app._execute_rename()
        self.assertEqual(self.snapshot(), {"NEW-IMAGE-2024-DONE.PNG": b"image"})
        self.app._undo_last_rename()
        self.assertEqual(self.snapshot(), {"old_photo__2024.jpg": b"image"})

    def test_reverse_sequence_combines_with_other_options_and_filter(self):
        self.add_file("a.jpg", b"A")
        self.add_file("b.JPG", b"B")
        self.add_file("c.png", b"C")
        self.app._load_files()
        self.configure(
            "reverse", "delete_text", "replace", "sequence", "prefix", "suffix", "regex", "case", "ext",
            entry_delete_text="a", entry_find="b", entry_replace="z",
            entry_base_name="photo", entry_start_num="9", entry_digits="2",
            entry_prefix="pre_", entry_suffix="_done", entry_regex="photo", entry_regex_replace="image",
            case_mode="upper", entry_new_ext="PNG", filter_ext="jpg,",
        )
        self.app._execute_rename()
        self.assertEqual(self.snapshot(), {"PRE_IMAGE09_DONE.PNG": b"B", "PRE_IMAGE10_DONE.PNG": b"A", "c.png": b"C"})
        self.app._undo_last_rename()
        self.assertEqual(self.snapshot(), {"a.jpg": b"A", "b.JPG": b"B", "c.png": b"C"})

    def test_failure_at_each_rename_stage_rolls_back_the_whole_batch(self):
        original_rename = os.rename
        for fail_at in range(1, 5):
            with self.subTest(fail_at=fail_at):
                self.add_file("a.txt", b"A")
                self.add_file("b.txt", b"B")
                self.app._load_files()
                self.configure("prefix", entry_prefix="new_")
                calls = 0

                def fail_once(source, target):
                    nonlocal calls
                    calls += 1
                    if calls == fail_at:
                        raise PermissionError("simulated locked file")
                    return original_rename(source, target)

                with patch("batch_rename.os.rename", side_effect=fail_once):
                    self.app._execute_rename()
                self.assertEqual(self.snapshot(), {"a.txt": b"A", "b.txt": b"B"})
                self.assertEqual(self.app.rename_history, [])
                (self.folder / "a.txt").unlink()
                (self.folder / "b.txt").unlink()

    def test_incomplete_rollback_keeps_recoverable_paths_for_undo(self):
        self.add_file("a.txt", b"A")
        self.add_file("b.txt", b"B")
        self.app._load_files()
        self.app.selection_mode = "files"
        self.configure("prefix", entry_prefix="new_")
        original_rename = os.rename
        calls = 0

        def fail_commit_and_one_restore(source, target):
            nonlocal calls
            calls += 1
            if calls in (3, 4):
                raise PermissionError("simulated temporary lock")
            return original_rename(source, target)

        with patch("batch_rename.os.rename", side_effect=fail_commit_and_one_restore):
            self.app._execute_rename()

        self.assertEqual(sorted(self.snapshot().values()), [b"A", b"B"])
        self.assertEqual(len(self.app.rename_history), 1)
        recovery = self.app.rename_history[0][0]["new_path"]
        self.assertTrue(Path(recovery).exists())
        self.assertIn(recovery, [f["path"] for f in self.app.files])
        self.assertIn(recovery, self.messages.showerror.call_args[0][1])

        self.app._undo_last_rename()
        self.assertEqual(self.snapshot(), {"a.txt": b"A", "b.txt": b"B"})
        self.assertEqual(self.app.rename_history, [])

    def test_failed_undo_rolls_back_and_can_be_retried_for_a_name_cycle(self):
        self.add_file("1.txt", b"one")
        self.add_file("2.txt", b"two")
        self.app._load_files()
        self.configure("reverse", "sequence", entry_digits="1")
        self.app._execute_rename()
        renamed = self.snapshot()
        original_rename = os.rename
        calls = 0

        def fail_once(source, target):
            nonlocal calls
            calls += 1
            if calls == 3:
                raise PermissionError("simulated locked undo")
            return original_rename(source, target)

        with patch("batch_rename.os.rename", side_effect=fail_once):
            self.app._undo_last_rename()
        self.assertEqual(self.snapshot(), renamed)
        self.assertEqual(len(self.app.rename_history), 1)
        self.app._undo_last_rename()
        self.assertEqual(self.snapshot(), {"1.txt": b"one", "2.txt": b"two"})
        self.assertEqual(self.app.rename_history, [])

    def test_incomplete_undo_rollback_keeps_updated_recovery_paths(self):
        self.add_file("a.txt", b"A")
        self.add_file("b.txt", b"B")
        self.app._load_files()
        self.configure("prefix", entry_prefix="new_")
        self.app._execute_rename()
        original_rename = os.rename
        calls = 0

        def fail_commit_and_one_restore(source, target):
            nonlocal calls
            calls += 1
            if calls in (3, 4):
                raise PermissionError("simulated temporary lock")
            return original_rename(source, target)

        with patch("batch_rename.os.rename", side_effect=fail_commit_and_one_restore):
            self.app._undo_last_rename()
        self.assertEqual(sorted(self.snapshot().values()), [b"A", b"B"])
        self.assertEqual(len(self.app.rename_history), 1)
        self.app._undo_last_rename()
        self.assertEqual(self.snapshot(), {"a.txt": b"A", "b.txt": b"B"})
        self.assertEqual(self.app.rename_history, [])

    def test_undo_refuses_a_replacement_file(self):
        self.add_file("a.txt", b"original")
        self.app._load_files()
        self.configure("prefix", entry_prefix="new_")
        self.app._execute_rename()
        (self.folder / "new_a.txt").rename(self.folder / "moved_original.txt")
        self.add_file("new_a.txt", b"unrelated")

        self.app._undo_last_rename()

        self.assertEqual(self.snapshot(), {"moved_original.txt": b"original", "new_a.txt": b"unrelated"})
        self.assertEqual(len(self.app.rename_history), 1)
        self.messages.showerror.assert_called_once()

    def test_missing_undo_source_is_reported_and_history_is_retained(self):
        self.add_file("a.txt")
        self.app._load_files()
        self.configure("prefix", entry_prefix="new_")
        self.app._execute_rename()
        (self.folder / "new_a.txt").unlink()
        self.app._undo_last_rename()
        self.assertEqual(len(self.app.rename_history), 1)
        self.messages.showerror.assert_called_once()

    def test_target_created_during_confirmation_is_preserved(self):
        self.add_file("a.txt", b"original")
        self.app._load_files()
        self.configure("prefix", entry_prefix="new_")

        def create_target(*args):
            self.add_file("new_a.txt", b"other")
            return True

        self.messages.askyesno.side_effect = create_target
        self.app._execute_rename()
        self.assertEqual(self.snapshot(), {"a.txt": b"original", "new_a.txt": b"other"})
        self.assertEqual(self.app.rename_history, [])

    def test_file_removed_after_loading_does_not_crash(self):
        source = self.add_file("a.txt")
        self.app._load_files()
        self.configure("prefix", entry_prefix="new_")
        source.unlink()
        self.app._execute_rename()
        self.assertEqual(self.app.rename_history, [])
        self.messages.showerror.assert_called_once()

    def test_removed_directory_is_reported_without_crashing(self):
        directory = self.folder / "removed"
        directory.mkdir()
        self.app.current_dir = str(directory)
        directory.rmdir()
        self.app._refresh_files()
        self.assertEqual(self.app.files, [])
        self.messages.showerror.assert_called_once()

    def test_batch_can_be_undone_in_multiple_steps(self):
        self.add_file("photo.jpg", b"image")
        self.app._load_files()
        self.configure("prefix", entry_prefix="new_")
        self.app._execute_rename()
        self.configure("ext", entry_new_ext="PNG")
        self.app._execute_rename()
        self.assertEqual(self.snapshot(), {"new_photo.PNG": b"image"})
        self.app._undo_last_rename()
        self.assertEqual(self.snapshot(), {"new_photo.jpg": b"image"})
        self.app._undo_last_rename()
        self.assertEqual(self.snapshot(), {"photo.jpg": b"image"})
        self.assertEqual(self.app.rename_history, [])

    def test_same_target_name_in_different_directories_is_allowed(self):
        directories = [self.folder / "first", self.folder / "second"]
        self.app.files = []
        self.app.selection_mode = "files"
        for index, directory in enumerate(directories):
            directory.mkdir()
            path = directory / "a.txt"
            path.write_bytes(str(index).encode())
            self.app.files.append({"name": path.name, "path": str(path)})
        self.app._refresh_files()
        self.configure("replace", entry_find="a", entry_replace="image")
        self.app._execute_rename()
        self.assertEqual((directories[0] / "image.txt").read_bytes(), b"0")
        self.assertEqual((directories[1] / "image.txt").read_bytes(), b"1")
        self.app._undo_last_rename()
        for index, directory in enumerate(directories):
            self.assertEqual((directory / "a.txt").read_bytes(), str(index).encode())

    def test_filter_keyword_and_extension_work_together(self):
        self.add_file("Keep_A.JPG", b"A")
        self.add_file("keep_B.txt", b"B")
        self.add_file("Other.JPG", b"C")
        self.app._load_files()
        self.configure("prefix", entry_prefix="new_", filter_ext=".jpg,", filter_keyword="keep")
        self.app._execute_rename()
        self.assertEqual(self.snapshot(), {"new_Keep_A.JPG": b"A", "keep_B.txt": b"B", "Other.JPG": b"C"})

    def test_cancelled_operation_changes_nothing(self):
        self.add_file("a.jpg")
        self.app._load_files()
        before = self.snapshot()
        self.messages.askyesno.return_value = False
        self.app._execute_rename()
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.app.rename_history, [])

    def test_no_features_or_no_matching_files_changes_nothing(self):
        self.add_file("a.jpg")
        self.app._load_files()
        self.configure()
        self.app._execute_rename()
        self.messages.showwarning.assert_called_once()
        self.configure("prefix", entry_prefix="new_", filter_ext="png")
        self.app._execute_rename()
        self.assertEqual(set(self.snapshot()), {"a.jpg"})
        self.messages.askyesno.assert_not_called()

    def test_selected_file_list_tracks_name_swaps_correctly(self):
        self.add_file("1.txt", b"one")
        self.add_file("2.txt", b"two")
        self.app._load_files()
        self.app.selection_mode = "files"
        self.app.current_dir = ""
        self.configure("reverse", "sequence", entry_digits="1")
        self.app._execute_rename()
        self.assertEqual([f["name"] for f in self.app.files], ["2.txt", "1.txt"])
        self.assertEqual([Path(f["path"]).read_bytes() for f in self.app.files], [b"one", b"two"])
        self.app._undo_last_rename()
        self.assertEqual([f["name"] for f in self.app.files], ["1.txt", "2.txt"])

    def test_preview_reports_collisions_without_modifying_files(self):
        self.add_file("a.txt", b"A")
        self.add_file("b.txt", b"B")
        self.app._load_files()
        self.configure("regex", entry_regex="^[ab]$", entry_regex_replace="same")
        self.app._preview_rename()
        self.assertEqual(self.snapshot(), {"a.txt": b"A", "b.txt": b"B"})
        self.messages.showerror.assert_called_once()
        self.messages.askyesno.assert_not_called()

    def test_invalid_regex_patterns_and_replacements(self):
        self.app.files = [{"name": "source.txt"}]
        for pattern, replacement in (("(", "x"), ("(source)", r"\2"), ("source", r"\x")):
            with self.subTest(pattern=pattern, replacement=replacement):
                self.configure("regex", entry_regex=pattern, entry_regex_replace=replacement)
                self.assertIsNone(self.app._generate_new_names())

    def test_mixed_extension_case_and_undo(self):
        originals = {
            "照片.jpg": b"lowercase",
            "mixed.JpG": b"mixed case",
            "ready.JPG": b"already uppercase",
            "untouched.png": b"filtered out",
        }
        for name, content in originals.items():
            self.add_file(name, content)
        self.app._load_files()
        self.app.filter_ext.get.return_value = ".jpg"

        self.app._execute_rename()

        self.assertEqual(
            set(os.listdir(self.folder)),
            {"照片.JPG", "mixed.JPG", "ready.JPG", "untouched.png"},
        )
        self.assertEqual(len(self.app.rename_history[0]), 2)
        for name, content in originals.items():
            target = Path(name).with_suffix(".JPG") if name != "untouched.png" else name
            self.assertEqual((self.folder / target).read_bytes(), content)
        self.messages.showerror.assert_not_called()

        self.app._undo_last_rename()

        self.assertEqual(set(os.listdir(self.folder)), set(originals))
        self.assertEqual(self.app.rename_history, [])
        self.assertEqual({f["name"] for f in self.app.files}, set(originals))

    def test_selected_files_keep_actual_case_after_refresh_and_undo(self):
        self.add_file("selected.jpg")
        self.app._load_files()
        self.app.selection_mode = "files"
        self.app.current_dir = ""

        self.app._execute_rename()

        self.assertEqual(os.listdir(self.folder), ["selected.JPG"])
        self.assertEqual(self.app.files[0]["name"], "selected.JPG")
        self.assertEqual(self.app.files[0]["path"], str(self.folder / "selected.JPG"))
        self.app._refresh_files()
        self.assertEqual(self.app.files[0]["name"], "selected.JPG")

        self.app._undo_last_rename()

        self.assertEqual(os.listdir(self.folder), ["selected.jpg"])
        self.assertEqual(self.app.files[0]["name"], "selected.jpg")
        self.assertEqual(self.app.files[0]["path"], str(self.folder / "selected.jpg"))

    def test_existing_other_file_is_not_overwritten(self):
        source = self.add_file("photo.png", b"source")
        existing = self.add_file("photo.JPG", b"keep this image")
        self.app._load_files()
        self.app.filter_ext.get.return_value = ".png"

        self.app._execute_rename()

        self.assertEqual(source.read_bytes(), b"source")
        self.assertEqual(existing.read_bytes(), b"keep this image")
        self.assertEqual(self.app.rename_history, [])
        self.messages.showerror.assert_called_once()
        self.assertIn("目标文件已存在", self.messages.showerror.call_args[0][1])

    def test_failed_rename_does_not_enter_undo_history(self):
        source = self.add_file("locked.jpg")
        self.app._load_files()

        with patch("batch_rename.os.rename", side_effect=PermissionError("file in use")):
            self.app._execute_rename()

        self.assertEqual(os.listdir(self.folder), ["locked.jpg"])
        self.assertEqual(self.app.rename_history, [])
        self.assertEqual(self.app.files[0]["path"], str(source))
        self.messages.showerror.assert_called_once()

    def test_ordinary_extension_change_and_undo(self):
        self.add_file("ordinary.png")
        self.app._load_files()

        self.app._execute_rename()
        self.assertEqual(os.listdir(self.folder), ["ordinary.JPG"])
        self.app._undo_last_rename()
        self.assertEqual(os.listdir(self.folder), ["ordinary.png"])
        self.messages.showerror.assert_not_called()

    def test_already_uppercase_is_unchanged(self):
        self.add_file("ready.JPG")
        self.app._load_files()

        with patch("batch_rename.os.rename") as rename:
            self.app._execute_rename()

        rename.assert_not_called()
        self.messages.askyesno.assert_not_called()
        self.assertEqual(self.app.rename_history, [])
        self.assertEqual(os.listdir(self.folder), ["ready.JPG"])

    def test_undo_does_not_overwrite_new_file_at_original_path(self):
        source = self.add_file("photo.png", b"original")
        self.app._load_files()
        self.app._execute_rename()
        source.write_bytes(b"new unrelated file")

        self.app._undo_last_rename()

        self.assertEqual(source.read_bytes(), b"new unrelated file")
        self.assertEqual((self.folder / "photo.JPG").read_bytes(), b"original")
        self.messages.showerror.assert_called_once()


if __name__ == "__main__":
    unittest.main()
