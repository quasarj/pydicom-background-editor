#!/usr/bin/perl

use Storable qw(store_fd);

# my $data = { foo => 1, bar => [2, 3, 4] };
## taken directly from the stderr of a real script run, so this
## should be a realistic test case
my $edits = {
  "edits" => [
    # {
    #   "arg1" => "113100",
    #   "arg2" => "",
    #   "op" => "set_tag",
    #   "tag" => "(0012,0064)[0](0008,0100)",
    #   "tag_mode" => "exact"
    # },
    # {
    #   "arg1" => "DCM",
    #   "arg2" => "",
    #   "op" => "set_tag",
    #   "tag" => "(0012,0064)[0](0008,0102)",
    #   "tag_mode" => "exact"
    # },
    {
      "arg1" => "Basic Application Confidentiality Profile",
      "arg2" => "",
      "op" => "set_tag",
      "tag" => "(0012,0064)[0](0008,0104)",
      "tag_mode" => "exact"
    },
  ],
    "from_file" => "/Users/quasar/Documents/DICOM/pathology/a3e6a5cc1bfbeda4bb229fa728486259",
    "to_file" => "./out.dcm"
};

## simulate the possible delay of the edit script
# sleep(3);

store_fd($edits, *STDOUT) or die "Can't store to stdout: $!";
# Note: no need to close STDOUT here.