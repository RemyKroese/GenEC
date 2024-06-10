#!/usr/bin/env python
import argparse
import utils
import genec


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Extract specific data from files and' +
        'and compare the differences between these 2 files based on the data.')

    parser.add_argument('-s', '--source', type=str, required=True,
                        help='Source file to extract data and compare.')
    parser.add_argument('-r', '--reference', type=str, required=True,
                        help='Reference file to extract data and compare.')

    return parser.parse_args()


def main():
    args = parse_arguments()
    source, ref = utils.read_files([args.source, args.reference])
    extractor = genec.Extractor()
    extractor.request_cluster_filter()
    extractor.request_text_filter()
    extractor.request_cluster_slicing()
    print('Extracting data from source file...')
    source_filtered_text = extractor.extract_from_data(source)
    print('Extracting complete.')
    print('Extracting data from reference file...')
    ref_filtered_text = extractor.extract_from_data(ref)
    print('Extracting complete.')

    comparer = genec.Comparer(source_filtered_text, ref_filtered_text)
    differences = comparer.compare()

    print(utils.create_ascii_table(differences))


if __name__ == '__main__':
    main()
